#Fernando Zanutto
import sys, os
import httplib2

#spotify api imports
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

#youtube api imports
import httplib2
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

youtube = None
client_credentials_manager = SpotifyClientCredentials('bf9c1626454341e79ba9244bb54cd44e', '2955a346f5af4c7b995f10857bc27c21')
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def ISOConverter(time):
    segundos=0
    minutos=0
    if "S" in time:
        cont=-2
        try:
            while True:
                t = int(time[cont])
                cont-=1
        except:
            pass

        temp=time[cont+1:-1]
        try:
            segundos = int(temp)
        except:
            print("erro:",time)
            x=input()

    if "M" in time:
        indice = time.index("M")
        try:
            if "H" not in time:
                minutos = int(time[2:indice])
            else:
                minutos = int(time[4:indice])
                minutos+= 60
        except:
            print("erro:",time)
            x=input()

    return segundos + minutos*60

def getSpotifyPlaylist(name):
    
    print(name)
    results = spotify.search(q=name, type='playlist')
    
    items = results['playlists']['items']

    if len(items) > 0:
        for item in items:
            print("ID:", items.index(item), " - Nome:", item['name'], " - Owner:", item['owner']['id'])

        selected = int(input("ID da playlist desejada: "))
        if selected < 0:
            return False
        playlist = items[selected]

        ownerId = playlist['owner']['id']
        playlistId = playlist['id']
        name = playlist['name']

        print("Spotify playlist name:", name)
        print("by:", ownerId)

        resultado = spotify.user_playlist_tracks(ownerId, playlistId)
        retorno = {"playlistId"     : playlistId,
                    "ownerId"       : ownerId,
                    "playlistName"   : name
        }
        musicas = []

        for item in resultado['items']:

            musica = item['track']

            nome = musica['name']
            artista = musica['artists'][0]['name']
            ms = musica['duration_ms']

            duracao = ms/1000

            musicas.append([nome, artista, duracao])

        retorno['items']=musicas
        return retorno

    return False


def youtubeConnection():
    global youtube

    CLIENT_SECRETS_FILE = "client_secrets.json"

    # This variable defines a message to display if the CLIENT_SECRETS_FILE is
    # missing.
    MISSING_CLIENT_SECRETS_MESSAGE = """
    WARNING: Please configure OAuth 2.0

    To make this sample run you will need to populate the client_secrets.json file
    found at:

       %s

    with information from the Developers Console
    https://console.developers.google.com/

    For more information about the client_secrets.json file format, please visit:
    https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
    """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       CLIENT_SECRETS_FILE))

    # This OAuth 2.0 access scope allows for full read/write access to the
    # authenticated user's account.
    YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,  message=MISSING_CLIENT_SECRETS_MESSAGE,  scope=YOUTUBE_READ_WRITE_SCOPE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    #TODO fazer com que o programa nao precise reiniciar qnd nao tem autenticação ainda
    if credentials is None or credentials.invalid:
      flags = argparser.parse_args()
      credentials = run_flow(flow, storage, flags)

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=credentials.authorize(httplib2.Http()))


def createYoutubePlaylist(playlist): #parameter = spotify playlist returned by getSpotifyPlaylist()
    global youtube
    name = playlist['playlistName']
    owner = playlist['ownerId']

    # This code creates a new, public playlist in the authorized user's channel.
    playlists_insert_response = youtube.playlists().insert(
      part="snippet,status",
      body=dict(
        snippet=dict(
          title=name,
          description="Spotify playlist by user: "+owner+"\n created using YouTube API v3 \nhttps://github.com/fernandozanutto/python/blob/master/spotify-youtube-playlist.py"
        ),
        status=dict(
          privacyStatus="public"
        )
      )
    ).execute()

    playlist_id = playlists_insert_response["id"]
    return playlist_id

def addVideoToPlaylist(playlist_id, video):
    print(video)
    pass
    playlist_items_insert_response = youtube.playlistItems().insert(
        part="snippet, contentDetails",
        body=dict(
            snippet=dict(
                playlistId=playlist_id,
                resourceId= dict(
                    kind="youtube#video",
                    videoId=video_id
                )
            )
        )
    ).execute()

def searchVideos(playlist): #parameter: array returned from getSpotifyPlaylist()
    global youtube

    retorno=[]

    for item in playlist['items']:

        name = item[0] + " - " + item[1]
        duracao1 = int(item[2])

        result = youtube.search().list(
            part="id, snippet",
            q=name,
            type="video"
        ).execute()
        
        videos =[]
        temp=[]
        for video in result['items']:

            videoId = video['id']['videoId']

            result2 = youtube.videos().list(
                part="contentDetails",
                id=videoId
            ).execute()
            d = result2['items'][0]['contentDetails']['duration']

            try:
                duracao = ISOConverter(d)
            except:
                print("Erro:",d)
                x=input("")

            videos.append([videoId, video['snippet']['title'], duracao])
            dif = abs(duracao1-duracao)

            temp.append(dif)
        print("Encontrado",videos[temp.index(min(temp))][1])
        retorno.append(videos[temp.index(min(temp))])

    return retorno



while True:
    x = input("Nome da playlist: ")
    playlist = getSpotifyPlaylist(x)
    if playlist:
        break
    else:
        print("Playlist não encontrada")

youtubeConnection()
playlistId = createYoutubePlaylist(playlist)
print("Criando playlist... Isso pode demorar um pouco...")
for video in searchVideos(playlist):
    addVideoToPlaylist(playlistId, video)
    
print("Done")
x=input()
