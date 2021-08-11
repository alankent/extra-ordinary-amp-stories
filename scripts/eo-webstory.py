from moviepy.editor import *
from os import listdir
from os.path import *
import shutil
import yaml
import glob


#with_fade = True
with_fade = False


# Example usage:
# fade_and_poster("test.mp4", "test-fade.mp4", "test-poster.jpg")

def fade_and_poster(input_mp4, output_mp4, output_jpg):

    #print("FADE: " + input_mp4 + " " + output_mp4 + " " + output_jpg)
    clip = VideoFileClip(input_mp4)
    #print(clip.duration)

    # The following writes the first frame to a file.
    clip.save_frame(output_jpg, t=0)

    # Create a clip with the last frame extended by 2 seconds
    end = clip.duration - 1.5/clip.fps
    freeze_duration = 2
    before = [clip.subclip(0,end)]
    freeze = [clip.to_ImageClip(end).set_duration(freeze_duration)]
    clip_with_freeze = concatenate_videoclips(before + freeze)
    #print(clip_with_freeze.duration)

    # Fade to black last 2 seconds, then remove most of it so there is a short partial fade
    final = clip_with_freeze.fx( vfx.fadeout, freeze_duration ).subclip(0, clip_with_freeze.duration - freeze_duration * 0.75)
    #final = clip_with_freeze.fx( vfx.fadeout, freeze_duration )
    #print(final.duration)

    # Save the new clip that ends with freeze and fade
    final.write_videofile(output_mp4)

    clip.close()


def extract_poster(input_mp4, output_jpg):
    clip = VideoFileClip(input_mp4)
    clip.save_frame(output_jpg, t=0)
    clip.close()



def header_html(episode_title, publisher_logo, publisher_name, poster_image):
    return r'''<!doctype html>
<html amp>
<head>
  <meta charset="utf-8">
  <title>''' + episode_title + r'''</title>
  <link rel="canonical" href="index.html">
  <meta name="viewport" content="width=device-width,minimum-scale=1,initial-scale=1">
  <style amp-boilerplate>body{-webkit-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-moz-animation:-amp-start 8s steps(1,end) 0s 1 normal both;-ms-animation:-amp-start 8s steps(1,end) 0s 1 normal both;animation:-amp-start 8s steps(1,end) 0s 1 normal both}@-webkit-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-moz-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-ms-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@-o-keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}@keyframes -amp-start{from{visibility:hidden}to{visibility:visible}}</style><noscript><style amp-boilerplate>body{-webkit-animation:none;-moz-animation:none;-ms-animation:none;animation:none}</style></noscript>
  <script async src="https://cdn.ampproject.org/v0.js"></script>
  <script async custom-element="amp-story" src="https://cdn.ampproject.org/v0/amp-story-1.0.js"></script>
  <style amp-custom>
  amp-story-page {
    background-color: #fff;
  }
  amp-story-grid-layer {
    padding: 0;
  }
  </style>
</head>
<body>
  <amp-story standalone
      title="''' + episode_title + r'''"
      publisher="''' + publisher_name + r'''"
      publisher-logo-src="''' + publisher_logo + r'''"
      poster-portrait-src="''' + poster_image + r'''"
      poster-square-src="''' + poster_image + r'''">
'''


def trailer_html():
    return "  </amp-story>\n<body>\n</html>\n"


def parse_input_directory(input_directory, episode):

    files = glob.glob(input_directory + "/EO-*/Recordings/" + episode + "-*")
    #print("Dir listing")
    #print(files)

    # Remove file extensions.
    files = map(lambda f: splitext(f)[0], files)
    #print("without extensions")
    #print(files)

    # Remove duplicates
    files = list(set(files))
    files.sort()
    #print("no duplicates")
    #print(files)

    directory = []
    for file in files:

        if "EO-Real" in file:
            continue
        
        bn = basename(file)
        path = os.path.dirname(file)
        #print(file + ".mp4")
        isJpeg = os.path.exists(file + ".jpg")
        isMp4 = os.path.exists(file + ".mp4")
        #print(isJpeg)
        #print(isMp4)

        if not isJpeg and not isMp4:
            # Skip any other files in directory.
            continue

        directory.append((bn, path, isJpeg, isMp4))

    #print("DIRECTORY")
    #print(directory)
    return directory


def create_web_story(input_projects_directory, episode, episode_title, publisher_name, publisher_logo_path, output_directory):

    files = parse_input_directory(input_projects_directory, episode)
    (first_name,_,_,_) = files[0]

    publisher_logo = "publisher-logo.png"
    poster_image = first_name + ".jpg"

    shutil.copy(publisher_logo_path, output_directory + "/" + publisher_logo)

    html = header_html(episode_title, publisher_logo, publisher_name, poster_image)

    for (name, path, isJpeg, isMp4) in files:

        print(">> " + name + " " + path, flush=True)

        html += '      <amp-story-page id="' + name + '">\n'
        html += '        <amp-story-grid-layer preset="2021-background" template="fill">\n'

        if isMp4:

            # If has mp4 and image, overwrite the static image!
            if with_fade:
                fade_and_poster(path + "/" + name + ".mp4", name + ".mp4", output_directory + "/" + name + ".jpg")
            else:
                extract_poster(path + "/" + name + ".mp4", output_directory + "/" + name + ".jpg")
                shutil.copy(path + "/" + name + ".mp4", output_directory + "/" + name + ".mp4")

            html += '          <amp-video src="' + name + '.mp4" width="868" height="1462" layout="fill"></amp-video>\n'

        else:

            # Static image only
            shutil.copy(path + "/" + name + ".jpg", output_directory + "/" + name + ".jpg")
            html += '          <amp-img src="' + name + '.jpg" width="868" height="1462" layout="fill"></amp-img>\n'

        html += '        </amp-story-grid-layer>\n'
        html += '      </amp-story-page>\n'

    html += trailer_html()

    html_file = open(output_directory + "/index.html", "wt")
    html_file.write(html)
    html_file.close()


def main():

    print("Specify one or more 'ep1' etc on command line")

    # Load up YAML file of all episodes
    config = None
    with open("episode-list.yaml", 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            for episode in sys.argv[1:]:
                
                print("== Episode " + episode, flush=True)
                
                ep = config['episodes'][sys.argv[1]]
                episode_title = ep['title']
                publisher_name = ep['author']
                publisher_logo_path = config['publisher_logo_png']
                input_projects_directory = config['input_projects_directory']
                output_directory = config['output_directory'] + "/" + episode

                if not os.path.exists(output_directory):
                    os.mkdir(output_directory)

                create_web_story(input_projects_directory, episode, episode_title, publisher_name, publisher_logo_path, output_directory)
                
        except yaml.YAMLError as exc:
            print(exc)

    
# Usage
main()
