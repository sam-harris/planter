import os
import stat
import base64
import logging
import paramiko
import imageio
import time
from dateutil.parser import parse
from dateutil.tz import gettz

from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.INFO)

server = "10.0.0.48"
user = "pi"
password = b"TWFya2VyMTI="

capture_local_file = "/app/camera/timelapse_capture.sh"
capture_remote_file = "/home/pi/timelapse_capture.sh"
local_output = "/app/output/pictures"
local_gif = "/app/output/gifs/plant_movie.gif"


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
    logging.info(f"There are {len(file_gen)} image(s) to transfer")
    for f in file_gen:
        logging.info(f"Transfering {f}")

        remote_file = f"/home/pi/camera/{f}"
        local_file = f"/app/output/pictures/{f}"
        # lets transfer this file

        sftp_client.get(remote_file, local_file)

        # now that we have the file delete it from the remote
        sftp_client.remove(remote_file)

    ssh.exec_command(f"sudo systemctl restart timelapse")
    logging.info("Processing Gif")
    images = []
    output_images = os.listdir(local_output)

    output_images.sort()

    for p in output_images:
        # we need to conver the - to : in the timezone
        # 2019-06-01T14-54-51EDT
        timestamp = p[: p.index("T")] + p[p.index("T") : -4].replace("-", ":")

        tzinfos = {"EDT": gettz("America/New_York")}
        yourdate = parse(timestamp, tzinfos=tzinfos)

        img = Image.open(f"/app/output/pictures/{p}")
        w, h = img.size

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("Arial.ttf", 72)
        text_w, text_h = draw.textsize(str(yourdate), font)
        draw.text(((w - text_w), h - text_h - 10), str(yourdate), (255, 8, 0), font=font)
        img.save(f"/app/output/pictures/{p}")

    for picture in output_images:
        images.append(imageio.imread(f"/app/output/pictures/{picture}"))
    imageio.mimwrite(local_gif, images)


if __name__ == "__main__":
    main()
