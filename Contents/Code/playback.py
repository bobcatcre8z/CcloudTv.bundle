import transcoder, common, common_fnc, livestreamer_fnc
import os, sys, re, time

# clients that dont require rtmp transcoding
RTMP_TRANSCODE_CLIENTS = ['Plex Web']

MP4_VIDEOS = ['googlevideo.com','googleusercontent.com','blogspot.com']
INCOMPATIBLE_URL_SERVICES = ['stream.mslive.in','stream.north.kz','stream.sportstv.com.tr','www.youtube.com','stream.canalsavoir.tv']

try:
	res_folder_path = os.getcwd().split("?\\")[1].split('Plug-in Support')[0]+"Plug-ins/CcloudTv.bundle/Contents/Resources/"
except:
	res_folder_path = os.getcwd().split("Plug-in Support")[0]+"Plug-ins/CcloudTv.bundle/Contents/Resources/"
if res_folder_path not in sys.path:
	sys.path.append(res_folder_path)

# Adapted from
#
# IPTV (Author: Cigaras)
# https://forums.plex.tv/index.php/topic/83083-iptvbundle-plugin-that-plays-iptv-streams-from-a-m3u-playlist/?hl=iptv
# https://github.com/Cigaras/IPTV.bundle
#
# Copyright � 2013-2015 Valdas Vaitiekaitis

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# Version 1.0.10
#
####################################################################################################
@route(common.PREFIX + '/createvideoclipobject', allow_sync=True)
def CreateVideoClipObject(url, title, thumb, summary, session, inc_container = False, transcode = False, dontUseURLServ=False, rating=None, content_rating=None, duration=None, studio=None, year=None, genres=None, actors=None, writers=None, directors=None):
	
	if rating != None:
		rating = float(rating)
	if duration != None:
		duration = int(duration)
	if year != None:
		year = int(year)
	genres_a = []
	if genres != None:
		for g in genres.split(','):
			if g != '':
				genres_a.append(g.strip())
			
	writers_a = []
	if writers != None:
		for w in writers.split(','):
			if w != '':
				writers_a.append(w.strip())
			
	directors_a = []
	if directors != None:
		for d in directors.split(','):
			if d != '':
				directors_a.append(d.strip())
		
	roles_a = []
	if actors != None:
		for r in actors.split(','):
			if r != '':
				roles_a.append(r.strip())
		
	vco = ''
	
	is_streamlink = livestreamer_fnc.CheckLivestreamer(url=url)
	if not inc_container and is_streamlink:
		vco = livestreamer_fnc.Qualities(title=title, url=url, summary=summary, thumb=thumb, art=thumb, is_streamlink=is_streamlink)
		if vco != None:
			if Prefs['debug']:
				Log("Using Livestreamer API")
			return vco
		else:
			if Prefs['debug']:
				Log("Not Using Livestreamer API")
	
	if '.mp3' in url or '.aac' in url or 'mmsh:' in url:
		container = Container.MP4
		audio_codec = AudioCodec.AAC
		
		if '.mp3' in url:
			container = 'mp3'
			audio_codec = AudioCodec.MP3
		elif '.aac' in url:
			container = 'aac'
			audio_codec = AudioCodec.AAC
			
		vco = TrackObject(
			key = Callback(CreateVideoClipObject, url = url, title = title, thumb = thumb, summary = summary, session = session, inc_container = True, dontUseURLServ=dontUseURLServ, rating=rating, duration=duration),
			rating_key = url,
			title = title,
			thumb = thumb,
			summary = summary,
			items = [
				MediaObject(
					parts = [
						PartObject(key=url)
					],
					container = container,
					audio_codec = audio_codec,
					audio_channels = 2
				)
			]
		)
	elif '.mp4' in url and '.m3u8' not in url and url.startswith('http'):
		# we will base64 encode the url, so that any conflicting url service does not interfere
		vco = MovieObject(
			url = "ccloudtv://" + E(JSON.StringFromObject(({"url":url, "title": title, "summary": summary, "thumb": thumb, "rating": rating, "duration": duration, "content_rating": content_rating, "studio": studio, "year": year, "genres": genres, "writers": writers, "directors": directors, "roles": actors}))),
			title = title,
			thumb = thumb,
			rating = rating,
			duration = duration,
			content_rating = content_rating,
			year = year,
			studio = studio,
			genres = genres_a,
			summary = summary
		)
	elif common_fnc.ArrayItemsInString(MP4_VIDEOS, url) and '.m3u8' not in url and url.startswith('http'):
		# we will base64 encode the url, so that any conflicting url service does not interfere
		vco = MovieObject(
			url = "ccloudtv://" + E(JSON.StringFromObject(({"url":url, "title": title, "summary": summary, "thumb": thumb, "rating": rating, "duration": duration, "content_rating": content_rating, "studio": studio, "year": year, "genres": genres, "writers": writers, "directors": directors, "roles": actors}))),
			title = title,
			thumb = thumb,
			rating = rating,
			duration = duration,
			content_rating = content_rating,
			year = year,
			studio = studio,
			genres = genres_a,
			summary = summary
		)
	elif '.m3u8' not in url and 'rtmp:' in url and transcode and Prefs['use_transcoder']: # transcode case
		
		#if inc_container:
		file = "file:///" + res_folder_path.replace('\\','/').replace(' ','%20') + "MyPreRoll.mp4"
		live_folder_path = Prefs['transcode_server_local']
		bool = transcoder.Transcoder(url, live_folder_path, session , '.m3u8', file, False, True, False)
		
		if bool:
			if 'Host' in Request.Headers:
				host = Request.Headers['Host']
				host = host.replace('-','.')
			else:
				host = None
			if Prefs['debug']:
				Log("Host ---------------- " + str(host))
			url = Prefs['transcode_server'] + session + '.m3u8'
			
		vco = VideoClipObject(
			key = Callback(CreateVideoClipObject, url = url, title = title, thumb = thumb, summary = summary, session = session, inc_container = True, transcode=transcode, dontUseURLServ=dontUseURLServ, rating=rating, duration=duration),
			#rating_key = url,
			url = url,
			title = title,
			summary = summary,
			thumb = thumb,
			rating = rating,
			duration = duration,
			items = [
				MediaObject(
					#container = Container.MP4,	 # MP4, MKV, MOV, AVI
					#video_codec = VideoCodec.H264, # H264
					#audio_codec = AudioCodec.AAC,  # ACC, MP3
					#audio_channels = 2,			# 2, 6
					#container = container,
					#audio_codec = audio_codec,
					parts = [PartObject(key = GetVideoURL(url = url, live = True, transcode=transcode, finalPlay=inc_container))],
					optimized_for_streaming = True
				)
			]
		)
	else:
		url_serv = None
		if not dontUseURLServ and not common_fnc.ArrayItemsInString(INCOMPATIBLE_URL_SERVICES, url):
			if Prefs['debug']:
				Log("Finding URLService for " + url)
			url_serv = URLService.ServiceIdentifierForURL(url)
		if url_serv <> None:
			if Prefs['debug']:
				Log("Using URLService for " + url)
			p = re.compile(ur'^((http[s]?|ftp):\/)?\/?([^:\/\s]+)((\/\w+)*\/)([\w\-\.]+[^#?\s]+)(.*)?(#[\w\-]+)?$')
			remote_host = re.search(p, url).group(3)
			vco = VideoClipObject(
				url = remote_host + "ccloudtv2://" + E(JSON.StringFromObject(({"url":url, "title": title, "summary": summary, "thumb": thumb, "rating": rating, "duration": duration}))),
				title = title,
				summary = summary,
				rating = rating,
				duration = duration,
				thumb = thumb
			)
		else:
			parts = []
			rangeX = 1
			if url.endswith('.ts') and inc_container: # for .ts segments add them as parts to have continuos playback
				rangeX = 1000
			for x in range(0,rangeX):
				po = PartObject(key = GetVideoURL(url = url, live = True, transcode=transcode, finalPlay=inc_container))
				parts.append(po)
				
			vco = VideoClipObject(
				key = Callback(CreateVideoClipObject, url = url, title = title, thumb = thumb, summary = summary, session = session, inc_container = True, dontUseURLServ=dontUseURLServ, rating=rating, duration=duration),
				rating_key = url,
				#url = url,
				title = title,
				summary = summary,
				thumb = thumb,
				rating = rating,
				duration = duration,
				items = [
					MediaObject(
						#container = Container.MP4,	 # MP4, MKV, MOV, AVI
						#video_codec = VideoCodec.H264, # H264
						#audio_codec = AudioCodec.AAC,  # ACC, MP3
						#audio_channels = 2,			# 2, 6
						#container = container,
						#audio_codec = audio_codec,
						parts = parts,
						optimized_for_streaming = True
					)
				]
			)

	if inc_container:
		return ObjectContainer(objects = [vco])
	else:
		return vco
		
####################################################################################################
def GetVideoURL(url, live, transcode, finalPlay, **kwargs):

	#url = 'http://wpc.c1a9.edgecastcdn.net/hls-live/20C1A9/cnn/ls_satlink/b_828.m3u8?Vd?u#bt!25'
	
	if '.m3u' in url and '.ts' in url:
		#return HTTPLiveStreamURL(url=url) # does not work - retrieves only single segment
		return PlayVideoLive(url=url) # playing .ts segments as PartObjects
	elif url.startswith('rtmp') and not transcode:
		if Prefs['debug']:
			Log.Debug('*' * 80)
			Log.Debug('* url before processing: %s' % url)
		#if url.find(' ') > -1:
		#	playpath = GetAttribute(url, 'playpath', '=', ' ')
		#	swfurl = GetAttribute(url, 'swfurl', '=', ' ')
		#	pageurl = GetAttribute(url, 'pageurl', '=', ' ')
		#	url = url[0:url.find(' ')]
		#	Log.Debug('* url_after: %s' % RTMPVideoURL(url = url, playpath = playpath, swfurl = swfurl, pageurl = pageurl, live = live))
		#	Log.Debug('*' * 80)
		#	return RTMPVideoURL(url = url, playpath = playpath, swfurl = swfurl, pageurl = pageurl, live = live)
		#else:
		#	Log.Debug('* url_after: %s' % RTMPVideoURL(url = url, live = live))
		#	Log.Debug('*' * 80)
		#	return RTMPVideoURL(url = url, live = live)
			Log.Debug('* url after processing: %s' % RTMPVideoURL(url = url, live = live))
			Log.Debug('*' * 80)
		return RTMPVideoURL(url = url, live = live)
	else:
		if transcode and finalPlay:
			time.sleep(10) # give some delay for transcoding to begin - remember output m3u8 is not instant

		return HTTPLiveStreamURL(url = url)

####################################################################################################
@indirect
def PlayVideoLive(url):

	return HTTPLiveStreamURL(url=url)
	#return Redirect(url)
	#return IndirectResponse(VideoClipObject, key=url, http_headers=http_headers)

	