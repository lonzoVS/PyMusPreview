import os
import sys
import subprocess
import argparse
import datetime
import shutil

DEFAULT_LENGTH = 10
DEFAULT_STARTTIME = 0
DEFAULT_FADESIZE = 5
DEFAULT_BITRATE = '320k'

# parse cmd parameters
parser = argparse.ArgumentParser(description='one of the python labs from uni')
parser.add_argument('-s', '--source',
                    help='source folder with audio files',
                    required=True)
parser.add_argument('-d', '--destination',
                    help='destination folder for created mp3 preview file')
parser.add_argument('-c', '--count',
                    help='number of files that will be included to preview mix',
                    default=0)
parser.add_argument('-l', '--length',
                    help='time in seconds of a segment to crop',
                    default=str(DEFAULT_LENGTH))
parser.add_argument('-st', '--starttime',
                    help='starting time in an audio file for cropping',
                    default=str(DEFAULT_STARTTIME))
params = parser.parse_args(sys.argv[1:])



#destination preparation
folder = str(params.source)
if params.destination is None:
    outputfile = os.path.join(folder, 'preview{}.mp3'.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))
    print('#####  Preview mix will be saved to {}  #####'.format(outputfile))
else:
    outputfile = str(params.destination)
    if not os.path.exists(outputfile):
        os.makedirs(outputfile, exist_ok=True)

#get list of .mp3 files in the source folder
audiofiles = [os.path.join(folder, file) for file in os.listdir(folder) if file.endswith('mp3')]

#check if ffmpeg.exe is in the same directory as script
ffmpeg = 'ffmpeg'
try:
    subprocess.Popen([ffmpeg], stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
except Exception:
    print("#####  Could not found ffmpeg.exe!  #####")
    exit()

#check and set count parameter
audioFilesNumber = len(audiofiles)
if params.count is 0:
    trackcount = audioFilesNumber
else:
    try:
        trackcount = int(params.count)
        if trackcount > audioFilesNumber:
            trackcount = audioFilesNumber
            print('#####  Count value is bigger than actual number of files and will be set to: {}  #####'.format(trackcount))
    except ValueError as e:
        trackcount = audioFilesNumber
        print('#####  Wrong count format, count will be set to: {}  #####'.format(trackcount))

#check and set starttime parameter
try:
    starttime = int(params.starttime)
except ValueError:
    starttime = DEFAULT_STARTTIME
    print('#####  Wrong start time format, count will be set to: {}  #####'.format(starttime))

# check and set length parameter
try:
    length = int(params.length)
except ValueError:
    length = DEFAULT_LENGTH
    print('#####  Wrong length format, count will be set to: {}  #####'.format(length))

#remove temporary folder if already exists
tempdir = '{}/tempAudioDir'.format(os.getcwd())
if os.path.exists(tempdir) and os.path.isdir(tempdir):
    shutil.rmtree(tempdir)

#create tempdir wich will hold temporary audio files
os.makedirs(tempdir)



number = 0
tempfiles = []
tempfile = '{}/temp.mp3'.format(tempdir)
try:
    for file in audiofiles[:trackcount]:
        print('Processing file: {}'.format(file))

        # ffmpeg cropping command
        subprocess.check_call([ffmpeg, '-y',
                               '-ss', str(starttime),
                               '-t', str(length),
                               '-i',
                               file,
                               '-acodec', 'copy',
                               tempfile],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

        tempfilePreview = '{}/temp{}.mp3'.format(tempdir, number)

        # ffmpeg fade in/out command
        fadeoption = 'afade=t=in:ss=0:d={},afade=t=out:st={}:d={}'.format(
            DEFAULT_FADESIZE, length - DEFAULT_FADESIZE, DEFAULT_FADESIZE)
        subprocess.check_call([ffmpeg, '-y',
                               '-i',
                               tempfile,
                               '-af',
                               fadeoption,
                               '-ab', DEFAULT_BITRATE,
                               tempfilePreview],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

        #we can remove tempfile after each itteration or use '-y' parameter in ffmpeg cropping command
        #to force ffmpeg overwrite temp file, since the file is in the temp folder, wich will get deleted
        #anyway in the finnaly block
        #os.remove(tempfile)

        tempfiles.append(tempfilePreview)
        number += 1

    #prepare string of files from temp files list for concatination command
    filestoconcat = '|'.join(tempfiles)

    # ffmpeg concatinating command,
    subprocess.check_call([ffmpeg, '-y',
                           '-i',
                           "concat:{}".format(filestoconcat),
                           '-acodec', 'copy',
                           outputfile],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

except Exception as e:
    print('#####  An error occured while processing files: {}  #####'.format(e))
finally:
    #cleanup temp folder
    shutil.rmtree(tempdir)

