#!/bin/bash
# quick script to run default gource config for cool git visualization
gource --hide progress --title 'MadVibes Bots' --seconds-per-day 3 --auto-skip-seconds 0.1 --file-idle-time 0 -1080x1080 --user-image-dir ./ --user-scale 0.6 \
    --multi-sampling \
    --key \
    --stop-at-end \
    --highlight-users \
    --file-idle-time 0 \
    --max-files 0 \
    --background-colour 000000 \
    --font-size 25 \
    --output-ppm-stream gource.ppm \
    --output-framerate 30
#ffmpeg -y -r 30 -f image2pipe -vcodec ppm -hwaccel cuda -i gource.ppm -vcodec h264_nvenc -preset slow -pix_fmt yuv420p -crf 1 -threads 0 -bf 0 gource-out.mp4 
ffmpeg -y -r 30 -f image2pipe -vcodec ppm -hwaccel cuda -i gource.ppm -vcodec libx264 -preset veryslow -pix_fmt yuv420p -crf 11 -threads 0 -bf 0 gource-out.mp4 
########################################################################################################
#   Copyright (C) 2022  Liam Coombs, Sam Tipper
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
