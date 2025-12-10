#!/bin/bash
cpcmp /opt/allemande/rooms/nsfw/.access.yml /opt/allemande/rooms/sanctuary/.access.yml
cpcmp /opt/allemande/rooms/nsfw/.access.yml /opt/allemande/rooms/astraea/.access.yml
TZ=Australia/Brisbane scene-time /opt/allemande/rooms/nsfw/Serenity\ Beach.m /opt/allemande/rooms/scene/Serenity\ Beach.txt /opt/allemande/rooms/scene/Serenity\ Beach.date /opt/allemande/rooms/scene/Serenity\ Beach.time
cpcmp /opt/allemande/config.sh ~/my/allemande/config_opal.sh
