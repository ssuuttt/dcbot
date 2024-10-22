import os
import re

from pytube import YouTube
import whisper
import logging



from pytube.innertube import _default_clients
from pytube import cipher

_default_clients["ANDROID"]["context"]["client"]["clientVersion"] = "19.08.35"
_default_clients["IOS"]["context"]["client"]["clientVersion"] = "19.08.35"
_default_clients["ANDROID_EMBED"]["context"]["client"]["clientVersion"] = "19.08.35"
_default_clients["IOS_EMBED"]["context"]["client"]["clientVersion"] = "19.08.35"
_default_clients["IOS_MUSIC"]["context"]["client"]["clientVersion"] = "6.41"
_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]

def get_throttling_function_name(js: str) -> str:
    """Extract the name of the function that computes the throttling parameter.

    :param str js:
        The contents of the base.js asset file.
    :rtype: str
    :returns:
        The name of the function used to compute the throttling parameter.
    """
    function_patterns = [
        r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&\s*'
        r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)',
        r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])\([a-z]\)',
    ]
    #logger.debug('Finding throttling function name')
    for pattern in function_patterns:
        regex = re.compile(pattern)
        function_match = regex.search(js)
        if function_match:
            #logger.debug("finished regex search, matched: %s", pattern)
            if len(function_match.groups()) == 1:
                return function_match.group(1)
            idx = function_match.group(2)
            if idx:
                idx = idx.strip("[]")
                array = re.search(
                    r'var {nfunc}\s*=\s*(\[.+?\]);'.format(
                        nfunc=re.escape(function_match.group(1))),
                    js
                )
                if array:
                    array = array.group(1).strip("[]").split(",")
                    array = [x.strip() for x in array]
                    return array[int(idx)]

    raise RegexMatchError(
        caller="get_throttling_function_name", pattern="multiple"
    )

cipher.get_throttling_function_name = get_throttling_function_name




SAMPLES = {
    "DALL·E 2 Explained by OpenAI": "https://www.youtube.com/watch?v=qTgPSKKjfVg",
    "Streamlit Shorts: How to make a select box by Streamlit": "https://www.youtube.com/watch?v=8-GavXeFlEA"
    }

MAX_VIDEO_LENGTH = 8*60


def sample_to_url(option):
    return SAMPLES.get(option)

def load_whisper_model():
    model = whisper.load_model('tiny', device='cpu')
    return model


def valid_url(url):
 return re.search(r'((http(s)?:\/\/)?)(www\.)?((youtube\.com\/)|(youtu.be\/))[\S]+', url)


def get_video_duration_from_youtube_url(url):
    logging.info(f"Getting video duration from {url}")
    yt = YouTube(url)
    return yt.length


def _get_audio_from_youtube_url(url):
    logging.info(f"Getting audio from {url}")
    yt = YouTube(url)
    if not os.path.exists('data'):
        os.makedirs('data')
    yt.streams.filter(only_audio=True).first().download(filename=os.path.join('data','audio.mp3'))


def _whisper_result_to_srt(result):
    text = []
    for i,s in enumerate(result['segments']):
        text.append(str(i+1))

        time_start = s['start']
        hours, minutes, seconds = int(time_start/3600), (time_start/60) % 60, (time_start) % 60
        timestamp_start = "%02d:%02d:%06.3f" % (hours, minutes, seconds)
        timestamp_start = timestamp_start.replace('.',',')     
        time_end = s['end']
        hours, minutes, seconds = int(time_end/3600), (time_end/60) % 60, (time_end) % 60
        timestamp_end = "%02d:%02d:%06.3f" % (hours, minutes, seconds)
        timestamp_end = timestamp_end.replace('.',',')        
        text.append(timestamp_start + " --> " + timestamp_end)

        text.append(s['text'].strip() + "\n")
            
    return "\n".join(text)


def transcribe_youtube_video(_model, url):
    _get_audio_from_youtube_url(url)
    options = whisper.DecodingOptions(fp16=False)
    result = _model.transcribe(os.path.join('data','audio.mp3'), **options.__dict__)
    result['srt'] = _whisper_result_to_srt(result)
    return result

def get_content_from_youtube_url(url):
    logging.info(f"Getting content from {url}")
    model =  load_whisper_model()
    logging.info(f"Model loaded")
    result = transcribe_youtube_video(model, url)
    logging.info(f"Transcription done")
    if result:
        return result['text'].strip()
    else:
        return None
