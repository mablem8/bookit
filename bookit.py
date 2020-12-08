# Usage: python3 bookit.py book_id /path/to/destination/
# Parameters:
#  book_id: book ID
#  /path/to/destination/: destination directory with sub-directories created:
#   /path/to/destination/
#    book-id/
#     progress/
#      page-ids.txt
#      done-page-ids.txt
#      todo-page-ids.txt
#      page-id-to-url.txt
#      page-id-to-order.txt
#      proxies.txt
#     page-images/
#      *.png
#     book-title.pdf
# Output:
#  .pdf file generated from page images

# Import Python modules
from bs4 import BeautifulSoup # HTML
from fpdf import FPDF         # PDF
from io import BytesIO        # IO
from PIL import Image         # PNG
import json                   # JSON
import os                     # file system
import re                     # regex for file name generation
import requests               # HTTP
import sys                    # accessing script arguments

# Initialize script arguments
bid = '' # book ID
dst = '' # destination directory for output files

# Parse script arguments
book_dir = ''
prog_dir = ''
imgs_dir = ''
title_and_author = ''
if len(sys.argv)==3:
  bid = sys.argv[1]
  if len(bid)!=12:
    print('Book ID is the wrong length (length of 12 expected). Exiting.')
    exit()
  title_and_author = bid # temporarily set to book ID
  dst = sys.argv[2]
  if dst[-1]!='/':
    dst += '/'
  if not os.path.isdir(dst):
    print('Destination directory '+dst+' does not exist. Exiting.')
    exit()
  book_dir = dst+bid+'/'
  if not os.path.isdir(book_dir):
    os.mkdir(book_dir)
  prog_dir = book_dir+'/progress/'
  if not os.path.isdir(prog_dir):
    os.mkdir(prog_dir)
  imgs_dir = book_dir+'/page-images/'
  if not os.path.isdir(imgs_dir):
    os.mkdir(imgs_dir)
else:
  print(\
   'Usage: '\
   'python3 bookit.py '\
   'book_id /path/to/destination/'\
  )
  exit()

# Variables
page_width_px   = 2048
default_proxies = './proxies.txt'

# Helper functions

# save string variable
def save_svar(svar_name,path_to_file):
  with open(path_to_file,mode='w') as ofile:
    ofile.write(svar_name)

# load string variable
def load_svar(path_to_file):
  out_svar = ''
  with open(path_to_file,mode='r') as ifile:
    out_svar = ifile.readlines()[0].strip()
  return out_svar

def save_list(list_name,path_to_file):
  with open(path_to_file,mode='w') as ofile:
    for e in list_name:
      ofile.write(e+'\n')

def load_list(path_to_file):
  out_list = []
  with open(path_to_file,mode='r') as ifile:
    raw_list = ifile.readlines()
    for e in raw_list:
      out_list.append(e.strip())
  return out_list

def save_dict(dict_name,path_to_file):
  with open(path_to_file,mode='w') as ofile:
    for key in dict_name.keys():
      ofile.write(key+':'+dict_name[key]+'\n')

def load_dict(path_to_file):
  out_dict = {}
  with open(path_to_file,mode='r') as ifile:
    raw_dict = ifile.readlines()
    for e in raw_dict:
      key_value = e.strip().split(':',1)
      out_dict[key_value[0]] = key_value[1]
  return out_dict

def format_proxy(proxy):
  if proxy==None:
    return None
  else:
    return {\
     'http':  'http://' +proxy,\
     'https': 'https://'+proxy \
    }

def update_head():
  req = requests.get('https://google.com')
  return {
   'Host': 'books.google.com',\
   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '+
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',\
   'Accept': '*/*',\
   'Accept-Language': 'en-US,en;q=0.5',\
   'Accept-Encoding': 'gzip, deflate',\
   'Connection': 'close',\
   'Cookie': 'NID='+str(req.cookies['NID'])\
  }

def update_proxy(proxies):
  proxy = proxies.pop(0)
  proxies.append(proxy)
  return proxy, proxies

# Main script

# Program data
proxies          = []
page_ids         = []
done_page_ids    = []
todo_page_ids    = []
page_id_to_url   = {}
page_id_to_order = {}

# Initialize global head variable
head = update_head()

# Check if progress exists
progress_exists = \
 os.path.exists(prog_dir+'proxies.txt')          and \
 os.path.exists(prog_dir+'page-ids.txt')         and \
 os.path.exists(prog_dir+'done-page-ids.txt')    and \
 os.path.exists(prog_dir+'todo-page-ids.txt')    and \
 os.path.exists(prog_dir+'page-id-to-url.txt')   and \
 os.path.exists(prog_dir+'page-id-to-order.txt')

# Populate program data
proxy = None
if progress_exists:
  title_and_author = load_svar(prog_dir+'title-and-author.txt')
  proxies          = load_list(prog_dir+'proxies.txt')
  page_ids         = load_list(prog_dir+'page-ids.txt')
  done_page_ids    = load_list(prog_dir+'done-page-ids.txt')
  todo_page_ids    = load_list(prog_dir+'todo-page-ids.txt')
  page_id_to_url   = load_dict(prog_dir+'page-id-to-url.txt')
  page_id_to_order = load_dict(prog_dir+'page-id-to-order.txt')
else:
  proxies   = load_list(default_proxies)
  page_data = requests.Request()
  try:
    page_data = requests.get(\
     'https://books.google.com/books?id='+bid+'&printsec=frontcover',\
     headers=head,proxies=format_proxy(proxy)\
    )
  except:
    try:
      head = update_head()
    except:
      pass # Keep the old head
    proxy, proxies = update_proxy(proxies)
    page_data = requests.get(\
     'https://books.google.com/books?id='+bid+'&printsec=frontcover',\
     headers=head,proxies=format_proxy(proxy)\
    )
  soup = BeautifulSoup(page_data.content, 'html.parser')
  title_and_author = soup.find_all('title')[0].contents[0][:-15]
  scripts = soup.find_all('script')
  string_response = ''
  try:
    string_response = '['+scripts[6].contents[0].split('_OC_Run')[1][1:-2]+']'
  except:
    string_response = '['+scripts[-4].contents[0].split('_OC_Run')[1][1:-2]+']'
  json_response = json.loads(string_response)
  for page_data in json_response[0]['page']:
    page_id = str(page_data['pid'])
    page_ids.append(page_id)
    page_id_to_url[page_id] = ''
    page_id_to_order[page_id] = str(page_data['order'])
  for page_data in json_response[3]['page']:
    page_id = str(page_data['pid'])
    page_id_to_url[page_id] = page_data['src']
  for page_id in page_ids:
    page_data_0 = requests.Request()
    try:
      page_data_0 = requests.get(\
       'https://books.google.com/books?id='+bid+'&pg='+page_id+'&jscmd=click3',\
       headers=head,proxies=format_proxy(proxy)\
      )
    except:
      try:
        head = update_head()
      except:
        pass # Keep the old head
      proxy, proxies = update_proxy(proxies)
      page_data_0 = requests.get(\
       'https://books.google.com/books?id='+bid+'&pg='+page_id+'&jscmd=click3',\
       headers=head,proxies=format_proxy(proxy)\
      )
    for page_data_1 in page_data_0.json()['page']:
      if \
       'src' in page_data_1.keys() and \
       page_data_1['src']!='' and \
       page_id_to_url[page_data_1['pid']]=='':
        page_id_to_url[page_data_1['pid']] = page_data_1['src']
  for page_id in page_ids:
    todo_page_ids.append(page_id)
  # Save progress
  save_svar(title_and_author,prog_dir+'title-and-author.txt')
  save_list(proxies,prog_dir+'proxies.txt')
  save_list(page_ids,prog_dir+'page-ids.txt')
  save_list(done_page_ids,prog_dir+'done-page-ids.txt')
  save_list(todo_page_ids,prog_dir+'todo-page-ids.txt')
  save_dict(page_id_to_url,prog_dir+'page-id-to-url.txt')
  save_dict(page_id_to_order,prog_dir+'page-id-to-order.txt')

# Attempt to download page images
failure_detected = False
for page_id in page_ids:
  if failure_detected:
    break
  if page_id not in todo_page_ids:
    continue
  page_url = page_id_to_url[page_id]
  if page_url == '':
    continue
  page_order = page_id_to_order[page_id]
  try_count = 0
  page_succ = False
  while (not page_succ) and try_count<3:
    try:
      page_image = requests.get(\
       page_url+'&w='+str(page_width_px),headers=head,\
       proxies=format_proxy(proxy)\
      )
      image = Image.open(BytesIO(page_image.content))
      image.save(imgs_dir+page_order+'.png')
      todo_page_ids.remove(page_id)
      done_page_ids.append(page_id)
      failure_detected = False
      # Loop update
      page_succ = True
    except:
      # Upon exception, need to update head and proxy regardless
      try:
        head = update_head()
      except:
        pass # Keep the old head
      proxy, proxies = update_proxy(proxies)
      # Save progress
      save_svar(title_and_author,prog_dir+'title-and-author.txt')
      save_list(proxies,prog_dir+'proxies.txt')
      save_list(page_ids,prog_dir+'page-ids.txt')
      save_list(done_page_ids,prog_dir+'done-page-ids.txt')
      save_list(todo_page_ids,prog_dir+'todo-page-ids.txt')
      save_dict(page_id_to_url,prog_dir+'page-id-to-url.txt')
      save_dict(page_id_to_order,prog_dir+'page-id-to-order.txt')
      # Abort upon repeated failure
      if failure_detected:
        break
      failure_detected = True
      # Loop update
      try_count += 1

# If above block exited without failure, then save progress
if not failure_detected:
  save_svar(title_and_author,prog_dir+'title-and-author.txt')
  save_list(proxies,prog_dir+'proxies.txt')
  save_list(page_ids,prog_dir+'page-ids.txt')
  save_list(done_page_ids,prog_dir+'done-page-ids.txt')
  save_list(todo_page_ids,prog_dir+'todo-page-ids.txt')
  save_dict(page_id_to_url,prog_dir+'page-id-to-url.txt')
  save_dict(page_id_to_order,prog_dir+'page-id-to-order.txt')

# If all of the pages downloaded, then collect all of the images into a PDF
if len(todo_page_ids)==0:
  # Get image file names
  page_image_files = sorted(os.listdir(imgs_dir),key=lambda x: int(x[:-4]))
  # Determine the largest page size needed
  pdf_w, pdf_h = Image.open(imgs_dir+page_image_files[0]).size
  for page_image_file in page_image_files:
    img_w, img_h = Image.open(imgs_dir+page_image_file).size
    pdf_w = max(pdf_w, img_w)
    pdf_h = max(pdf_h, img_h)
  # Initialize the PDF
  pdf = FPDF(orientation='portrait',unit='pt',format=(pdf_w,pdf_h))
  # Populate the PDF
  for page_image_file in page_image_files:
    pdf.add_page()
    img_w, img_h = Image.open(imgs_dir+page_image_file).size
    pdf.image(imgs_dir+page_image_file,x=0,y=0,w=img_w,h=img_h)
  # PDF file name
  pdf_file_name = \
   re.sub('[^0-9a-z]+', '-', title_and_author.strip().lower()).strip('-')+'.pdf'
  pdf.output(name=book_dir+pdf_file_name,dest='F')
else:
  print('Some page images not downloaded, try running the script again')
  print(\
   ' (it will try to download only the missing pages and make the PDF on'+\
   ' success)'\
  )
