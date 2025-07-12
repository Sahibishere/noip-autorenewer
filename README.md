# noip-renewer

![GitHub last commit](https://img.shields.io/github/last-commit/simao-silva/noip-renewer?style=for-the-badge)
![GitHub issues](https://img.shields.io/github/issues/simao-silva/noip-renewer?style=for-the-badge)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/simao-silva/noip-renewer/docker-build-alpine.yml?label=Alpine%20build&style=for-the-badge)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/simao-silva/noip-renewer/docker-build-debian.yml?label=Debian%20build&style=for-the-badge)
![Docker Pulls](https://img.shields.io/docker/pulls/simaofsilva/noip-renewer?style=for-the-badge)
![Docker Image Size (tag)](https://img.shields.io/docker/image-size/simaofsilva/noip-renewer/alpine?label=Alpine%20image%20size&style=for-the-badge)
![Docker Image Size (tag)](https://img.shields.io/docker/image-size/simaofsilva/noip-renewer/debian?label=Debian%20image%20size&style=for-the-badge)
[![renovate](https://img.shields.io/badge/renovate-enabled-brightgreen.svg?style=for-the-badge)](https://renovatebot.com)

:uk:: Renewing No-IP hosts by browser automation. Renews all hosts available for confirmation, without any user interaction with a browser. <br/>
# This is a script which run using github actions once a month to renew your no ip free hostname
  # Instructions to run manually use the actions tab and run the Renew No-IP Workflow
    # You will need to set action secrets by forking this repository and include the following DOCKERHUB_TOKEN, DOCKERHUB_USERNAME, NOIP_PASSWORD, NOIP_TOTP_KEY, and NOIP_USERNAME
      # All of the values that you need are pretty self explantory and explained by the name. For the DOCKERHUB_TOKEN, you will have to create a personal access token on your hub.docker.com account by going to settings and give read/write access to this repository. Another clarification is that the NOIP_TOTP_KEY is the 2 factor authentication key you get in the very beginning when you are enabling 2fa by authenticator app, you can export your 2fa through many authenticator apps and use that to see what the TOTP key is to enter as the value.
