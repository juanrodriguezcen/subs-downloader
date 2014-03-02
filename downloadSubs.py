import os
import re
import bs4 as bs
import urllib2
import urllib
import shutil
import rarfile
import zipfile

root_path = 'D:\Test\PythonDownloadSubtitles\PythonDownloadSubs\Series'
temp_subs_folder = 'D:\PythonProjects\DownloadSubtitles\subs'
subsgroups_to_use = ['argenteam', 'thesubfactory', 'substeam']



def downloadSubtitle(video_file, video_folder, show, season, episode, quality, group, is_proper):
  #Get a list of results going through the multiple pages (results are paginated)
  page_iter = 1
  title_divs = []
  description_divs = []
  while 1:
    url = "http://subdivx.com/index.php?accion=5&buscar=" + show.replace(" ", "+") + "+s" + str(season).zfill(2) + "e" + str(episode).zfill(2) + "&masdesc=&idusuario=&nick=&oxfecha=&oxcd=&oxdown=&pg=" + str(page_iter)
    page = urllib2.urlopen(url)
    content = page.read()

    soup = bs.BeautifulSoup(content)
    title_divs_iter = soup.find_all('div', {'id': 'menu_detalle_buscador'})
    description_divs_iter = soup.find_all('div', {'id': 'buscador_detalle'})

    if len(title_divs_iter) == 0 or len(description_divs_iter) == 0:
        break

    for td in title_divs_iter:
      title_divs.append(td)
    for dd in description_divs_iter:
      description_divs.append(dd)

    page_iter = page_iter + 1

  #We have the divs with the descriptions and links, we have to find the one we want
  subtitle_downloaded = False
  for idx, title_div in enumerate(title_divs):
    title_div_str = title_divs[idx].text.encode('utf-8')
    description_div_str = description_divs[idx].text.encode('utf-8')
    #Check that the name of the sub contains the episode name sXXeXX
    if (('s' + season + 'e' + episode) in title_div_str.lower()) and quality.lower() in description_div_str.lower() and group.lower() in description_div_str.lower() and (not is_proper or 'proper' in description_div_str.lower()):
      for sub_group in subsgroups_to_use:
        if sub_group in description_div_str.lower():
            try:
                details_page_url = str(title_divs[idx].find_all('a')[0]['href'])
            
                #We found a subtitle that matches the quality, the ripping group and its from one of our wanted subs groups
                #We download the file and try to process it, if anything fails we'll keep tyring with the next result
                page = urllib2.urlopen(details_page_url)
                content = page.read()
                soup = bs.BeautifulSoup(content )
                download_tag = soup.find_all('a', text= re.compile('^Bajar sub'))
                download_link = str(download_tag[0]['href']) #this is the download link

                redirected_url = urllib2.urlopen(download_link).geturl()
                filename = redirected_url.split('/')[-1]
                urllib.urlretrieve(redirected_url, os.path.join(temp_subs_folder, os.path.join(temp_subs_folder, filename)))

                #the file is downloaded, so we unpack its contents and process them
                #Create temp folder for the extracted subs
                extracted_subs_path = os.path.join(temp_subs_folder, 'extracted_subs')
                if  os.path.exists(extracted_subs_path):
                  shutil.rmtree(extracted_subs_path)

                os.makedirs(extracted_subs_path)

                #Check if its a rar or a zip file and deal with them
                if filename.endswith(".rar"):
                  rf = rarfile.RarFile(os.path.join(temp_subs_folder, filename))
                  rf.extractall(extracted_subs_path)
                elif filename.endswith(".zip"):
                  with zipfile.ZipFile(os.path.join(temp_subs_folder, filename)) as zf:
                    zf.extractall(extracted_subs_path)
                else:
                  raise Exception("unsupported file type")

                #Get the name of all the .srt files in the extracted subs directory
                sub_files = [f for f in os.listdir(extracted_subs_path) if (os.path.isfile(os.path.join(extracted_subs_path, f)) and str(f).endswith(".srt"))]
            
                #if its only one file we just use that one, if not we check the one with the correct quality
                if len(sub_files) == 1:
                    shutil.move(os.path.join(extracted_subs_path, sub_files[0]), os.path.join(video_folder, video_file.replace(".mkv", ".srt")))
                    subtitle_downloaded = True
                else:
                    for sub_file in sub_files:
                        if quality.lower() in sub_file.lower() and (not is_proper or 'proper' in sub_file.lower()):
                            shutil.move(os.path.join(extracted_subs_path, sub_file), os.path.join(video_folder, video_file.replace(".mkv", ".srt")))
                            subtitle_downloaded = True


                #delete the rar file

                if subtitle_downloaded:
                    break;
            except:
                pass # dont do anything, just go to the following entry

    if subtitle_downloaded:
        break;

  return subtitle_downloaded

                       



for root, dirs, files in os.walk(root_path):
  for file in files:
    if (file.endswith(".mkv") or file.endswith(".avi")) and not os.path.isfile(os.path.join(root, file.replace(".mkv", ".srt"))):
        name_parts = re.findall(r"""(.*)          # Title
                                [ .]
                                S(\d{1,2})    # Season
                                E(\d{1,2})    # Episode
                                [ .a-zA-Z]*  # Space, period, or words like PROPER/Buried
                                (\d{3,4}p)?   # Quality
                                [^-]*
                                -(.*)   # Group (dimension, killers, etc)
                                \.[mkv|avi]
                    """, file, re.VERBOSE)

        if len(name_parts) == 1 and len(name_parts[0])== 5:
          show = name_parts[0][0].replace('.', ' ')
          season = name_parts[0][1]
          episode = name_parts[0][2]
          quality = name_parts[0][3]
          group = name_parts[0][4]
          is_proper = 'proper' in file;
          print '--------------------'
          print 'Show: '+ name_parts[0][0].replace('.', ' ')
          print 'Season: ' + name_parts[0][1]
          print 'Episode:' + name_parts[0][2]
          print 'Quality: ' + name_parts[0][3]
          print 'Group: '+ name_parts[0][4]
          success = downloadSubtitle(file, root, show, season, episode, quality, group, is_proper)
          if success:
            print 'SUBTITLE DOWNLOADED!!'
          else:
            print 'Subtitle not found';


#delete all the zip and rar files downloaded by the script
aux_files = [f for f in os.listdir(temp_subs_folder) if (os.path.isfile(os.path.join(temp_subs_folder, f)))]
for af in aux_files:
    os.remove(os.path.join(temp_subs_folder, af))