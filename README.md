# docker-basics

This repo contains materials for my 2019 March 23 presentation **"A Beginner’s Guide to Docker (for Data Science or otherwise)"** at the Data Science with Python meetup (see [here](https://www.meetup.com/League-of-Extraordinary-Algorithms/events/259583765/) or [here](https://www.meetup.com/socialdatascience/events/259587939/) for the event notices).

Contents:
```
$ tree -L 1 -F
.
├── README.md
├── basic-demo/         <-- files used in "Demo: Outside and Inside Containers"
├── basic-demo.md       <-- steps for slide "Demo: Outside and Inside Containers"
├── dat-sci-demo/       <-- files used in "Demo: Docker for Data Science"
├── dat-sci-demo.md     <-- steps for slide "Demo: Docker for Data Science"
├── slides.pdf          <-- the presentation slides
└── vm-setup.md         <-- initial setup steps on the VM used for the demos
```

See `slides.pdf` for the slides used in the presentation.

The file `vm-setup.md` documents a few preliminary steps taken on the VM used in the demos (for the early part of the first demo where the sample app is run outside a container).

The first demo consists of running a simple Python Flask application both outside and inside Docker containers. This demo introduces the important basic Docker commands and shows how containers run as isolated child processes. The commands executed in the first demo are described in `basic-demo.md`, using the files in subdirectory `basic-demo/`.

The second demo shows how different versions of a trained model can be run in containers. The commands executed in the second demo are described in `dat-sci-demo.md`, using the files in subdirectory `dat-sci-demo/`.

Because this is a basic introduction to Docker, I have purposely eschewed the use of [docker-compose](https://docs.docker.com/compose/). `docker-compose` makes starting / stopping / managing containers much more convenient than plain `docker` commands. However, when first learing Docker it is best to avoid the extra layer of abstraction that `docker-compose` commands bring.
