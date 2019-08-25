import base64
import logging
import os
import stat
from multiprocessing import Pool

from time import sleep
from random import randint

import imageio
import paramiko
from dateutil.parser import parse
from dateutil.tz import gettz
from PIL import Image, ImageDraw, ImageFont


logging.basicConfig(
    format="%(processName)s |%(process)d| %(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.INFO
)

server = "10.0.0.48"
user = "pi"
password = b"TWFya2VyMTI="

capture_local_file = "/app/camera/timelapse_capture.sh"
capture_remote_file = "/home/pi/timelapse_capture.sh"
local_output = "/app/output/pictures"
local_gif = "/app/output/gifs/plant_movie.gif"

connection = None


def get_connection():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logging.info(f"Connecting to {server}")
    ssh.connect(server, username=user, password=base64.b64decode(password))
    logging.info(f"Creating SFTP to {server}")
    sftp_client = ssh.open_sftp()
    return sftp_client


# to be called in worker process
def init_worker():
    global connection
    sleep(randint(0, 5))
    connection = get_connection()


def do_work(f):

    global connection
    logging.info(f"Transfering {f}")

    remote_file = f"/home/pi/camera/{f}"
    local_file = f"/app/output/pictures/{f}"
    # lets transfer this file

    connection.get(remote_file, local_file)
    logging.info(f"Done Transfering {f}")
    # now that we have the file delete it from the remote
    connection.remove(remote_file)
    logging.info(f"Deleted {f} on Remote")

    # we need to conver the - to : in the timezone
    # 2019-06-01T14-54-51EDT
    timestamp = f[: f.index("T")] + f[f.index("T") : -4].replace("-", ":")

    tzinfos = {"EDT": gettz("America/New_York")}
    yourdate = parse(timestamp, tzinfos=tzinfos)

    img = Image.open(f"/app/output/pictures/{f}")
    w, h = img.size

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("Arial.ttf", 72)
    text_w, text_h = draw.textsize(str(yourdate), font)
    draw.text(((w - text_w), h - text_h - 10), str(yourdate), (255, 8, 0), font=font)
    img.save(f"/app/output/pictures/{f}")
    logging.info(f"Done adding Timestamp to {f}")

    return True


def main():

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logging.info(f"Connecting to {server}")
    ssh.connect(server, username=user, password=base64.b64decode(password))

    logging.info(f"Creating SFTP to {server}")
    sftp_client = ssh.open_sftp()

    ssh.exec_command(f"sudo touch /tmp/stop_timelapse")
    ssh.exec_command(f"sudo systemctl stop timelapse")

    # lets put our current version of the file in the necessarsy location
    put_file = sftp_client.put(capture_local_file, capture_remote_file)
    sftp_client.chmod(capture_remote_file, put_file.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # who knows how many files there are so lets get them
    file_gen = sftp_client.listdir("/home/pi/camera")
    remaining = len(file_gen)
    logging.info(f"There are {remaining} image(s) to transfer")

    with Pool(processes=4, initializer=init_worker, maxtasksperchild=2) as p:
        p.map(do_work, file_gen)
    logging.info("Done Transferring")

    ssh.exec_command(f"sudo systemctl restart timelapse")
    logging.info("Processing Gif")
    images = []
    output_images = os.listdir(local_output)

    output_images.sort()

    for picture in output_images:
        # print(psutil.virtual_memory())

        timestamp = picture[: picture.index("T")] + picture[picture.index("T") : -4].replace("-", ":")
        tzinfos = {"EDT": gettz("America/New_York")}
        yourdate = parse(timestamp, tzinfos=tzinfos)
        # if this is between 10 am and 2 pm use it to get the best possible light
        if 12 <= yourdate.hour <= 12:
            images.append(imageio.imread(f"/app/output/pictures/{picture}"))
    imageio.mimwrite(local_gif, images)


if __name__ == "__main__":

    main()
