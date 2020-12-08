# Usage: python3 get_page_images.py book_id /path/to/destination/
# Parameters:
#  book_id: book ID
#  destination: destination directory
# Output:
#  .pdf file generated from page images

# Import Python modules
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import json
import os
import requests

# Initialize script arguments
bid = '' # book ID
dst = '' # destination directory for output files

# Parse script arguments
if len(sys.argv)==3:
  bid = sys.argv[1]
  if(len(bid)!=12):
    print('Book ID is the wrong length')
    print(\
     'Usage: '\
     'python3 get_page_images.py '\
     'book_id /path/to/destination/'\
    )
    exit()
  dst = sys.argv[2]
  if dst[-1] != '/':
    dst += '/'
  if !os.path.isdir(dst):
    os.mkdir(dst)
  if !os.path.isdir(dst+'progress/'):
    os.mkdir(dst+'progress/')
  if !os.path.isdir(dst+'page-images/'):
    os.mkdir(dst+'page-images/')
else:
  print(\
   'Usage: '\
   'python3 get_page_images.py '\
   'book_id /path/to/destination/'\
  )
  exit()

# Variables
page_width_px = 2048
proxy_file = './proxies.txt'

# Helper functions

def write_list_to_file(list_name,file_name):
  with open(dst+file_name+'.txt',mode='w') as ofile:
    for e in list_name:
      ofile.write(e+'\n')

def read_list_from_file(file_name):
  out_list = []
  with open(dst+file_name+'.txt',mode='r') as ifile:
    raw_list = ifile.readlines()
    for e in raw_list:
      out_list.append(e.strip())
  return out_list

def write_dict_to_file(dict_name,file_name):
  with open(dst+file_name+'.txt',mode='w') as ofile:
    for key in dict_name.keys():
      ofile.write(key+':'+dict_name[key]+'\n')

def read_dict_from_file(file_name):
  out_dict = {}
  with open(dst+file_name+'.txt',mode='r') as ifile:
    raw_dict = ifile.readlines()
    for e in raw_dict:
      key_value = e.strip().split(':',1)
      out_dict[key_value[0]] = key_value[1]
  return out_dict

# Main script

page_ids = []
done_page_ids = []
todo_page_ids = []
page_id_to_url = {}
page_id_to_order = {}

req = requests.get('https://google.com')
head = {
 'Host': 'books.google.com',\
 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',\
 'Accept': '*/*',\
 'Accept-Language': 'en-US,en;q=0.5',\
 'Accept-Encoding': 'gzip, deflate',\
 'Connection': 'close',\
 'Cookie': 'NID='+str(req.cookies['NID'])\
}

# Check if progress exists
progress_exists = \
 os.path.exists(dst+'page-ids.txt') and \
 os.path.exists(dst+'done-page-ids.txt') and \
 os.path.exists(dst+'todo-page-ids.txt') and \
 os.path.exists(dst+'page-id-to-url.txt') and \
 os.path.exists(dst+'page-id-to-order.txt')

if progress_exists:
  page_ids = read_list_from_file('page-ids')
  done_page_ids = read_list_from_file('done-page-ids')
  todo_page_ids = read_list_from_file('todo-page-ids')
  page_id_to_url = read_dict_from_file('page-id-to-url')
  page_id_to_order = read_dict_from_file('page-id-to-order')
else:
  page_data = requests.get('https://books.google.com/books?id=o5O7j1g0rdAC&printsec=frontcover',headers=head)
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
    page_id = page_data['pid']
    page_ids.append(page_id)
    page_id_to_url[page_id] = ''
    page_id_to_order[page_id] = str(page_data['order'])
  for page_data in json_response[3]['page']:
    page_id = page_data['pid']
    page_id_to_url[page_id] = page_data['src']
  for page_id in page_ids:
    page_data_0 = requests.get('https://books.google.com/books?id=o5O7j1g0rdAC&pg='+str(page_id)+'&jscmd=click3',headers=head)
    for page_data_1 in page_data_0.json()['page']:
      if 'src' in page_data_1.keys() and page_data_1['src']!='' and page_id_to_url[page_data_1['pid']]=='':
        page_id_to_url[page_data_1['pid']] = page_data_1['src']
  for page_id in page_ids:
    todo_page_ids.append(page_id)
  # Save progress
  write_list_to_file(page_ids,'page-ids')
  write_list_to_file(done_page_ids,'done-page-ids')
  write_list_to_file(todo_page_ids,'todo-page-ids')
  write_dict_to_file(page_id_to_url,'page-id-to-url')
  write_dict_to_file(page_id_to_order,'page-id-to-order')

# Attempt to download page images
failure_detected = False
for page_id in page_ids:
  if page_id not in todo_page_ids:
    continue
  page_url = page_id_to_url[page_id]
  if page_url == '':
    continue
  page_order = page_id_to_order[page_id]
  try:
    page_image = requests.get(page_url+'&w='+str(page_width_px),headers=head)
    image = Image.open(BytesIO(page_image.content))
    image.save(dst+page_order+'.png')
    todo_page_ids.remove(page_id)
    done_page_ids.append(page_id)
    failure_detected = False
  except:
    # Save progress
    write_list_to_file(page_ids,'page-ids')
    write_list_to_file(done_page_ids,'done-page-ids')
    write_list_to_file(todo_page_ids,'todo-page-ids')
    write_dict_to_file(page_id_to_url,'page-id-to-url')
    write_dict_to_file(page_id_to_order,'page-id-to-order')
    # Abort upon repeated failure
    if failure_detected:
      break
    failure_detected = True
    # Try to refresh head
    try:
      req = requests.get('https://google.com')
      head = {
       'Host': 'books.google.com',\
       'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',\
       'Accept': '*/*',\
       'Accept-Language': 'en-US,en;q=0.5',\
       'Accept-Encoding': 'gzip, deflate',\
       'Connection': 'close',\
       'Cookie': 'NID='+str(req.cookies['NID'])\
      }
    except:
      break

# Save progress
write_list_to_file(page_ids,'page-ids')
write_list_to_file(done_page_ids,'done-page-ids')
write_list_to_file(todo_page_ids,'todo-page-ids')
write_dict_to_file(page_id_to_url,'page-id-to-url')
write_dict_to_file(page_id_to_order,'page-id-to-order')


