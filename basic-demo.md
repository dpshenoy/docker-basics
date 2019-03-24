The steps demonstrated here provide a basic introduction to building and running Docker containers, with discussion and commentary along the way about how containerized apps run as isolated child processes on the host machine. For more details on each of the docker commands used here, the best place to go is the [command line reference](https://docs.docker.com/engine/reference/commandline/cli/) section of https://docs.docker.com

The host machine is a VM running Ubuntu linux:
```
root@docker-s-1vcpu-1gb-sfo2-01:~# hostnamectl
   Static hostname: docker-s-1vcpu-1gb-sfo2-01
         Icon name: computer-vm
           Chassis: vm
        Machine ID: 549bf0cb1c3144f25830d4b85c9553b3
           Boot ID: 37c20d8e54454565b910a6766d63f7c3
    Virtualization: kvm
  Operating System: Ubuntu 18.04.2 LTS
            Kernel: Linux 4.15.0-45-generic
      Architecture: x86-64
```

This VM is a DigitalOcean droplet created using the convenient [Docker One-Click Application](https://www.digitalocean.com/docs/one-clicks/docker/) image which DigitalOcean provides. It comes with Docker pre-installed and enabled as a [systemd](https://wiki.debian.org/systemd) service so that upon launching of the VM the docker daemon is already up and running:
```
root@docker-s-1vcpu-1gb-sfo2-01:~# systemctl status docker
● docker.service - Docker Application Container Engine
   Loaded: loaded (/lib/systemd/system/docker.service; enabled; vendor preset: enabled)
   Active: active (running) since Fri 2019-03-22 21:29:20 UTC; 20min ago
     Docs: https://docs.docker.com
 Main PID: 833 (dockerd)
    Tasks: 8
   CGroup: /system.slice/docker.service
           └─833 /usr/bin/dockerd -H fd://
```

Note the mention of a **CGroup** in the output. **Control groups** are one of the [key Linux technologies used to make containers](https://docs.docker.com/engine/docker-overview/#control-groups):
> A cgroup limits an application to a specific set of resources. Control groups allow Docker Engine to share available hardware resources to containers and optionally enforce limits and constraints. For example, you can limit the memory available to a specific container.

Another way to confirm Docker is installed and running:
```
root@docker-s-1vcpu-1gb-sfo2-01:~# docker version
Client:
 Version:           18.09.2
 API version:       1.39
 Go version:        go1.10.6
 Git commit:        6247962
 Built:             Sun Feb 10 04:13:47 2019
 OS/Arch:           linux/amd64
 Experimental:      false

Server: Docker Engine - Community
 Engine:
  Version:          18.09.2
  API version:      1.39 (minimum version 1.12)
  Go version:       go1.10.6
  Git commit:       6247962
  Built:            Sun Feb 10 03:42:13 2019
  OS/Arch:          linux/amd64
  Experimental:     false
```

Note that this VM's version of Ubuntu linux comes with **Python 3** pre-installed, while **Python 2** is [not installed](https://lists.ubuntu.com/archives/ubuntu-devel-announce/2017-December/001234.html):
```
root@docker-s-1vcpu-1gb-sfo2-01:~# python3 --version
Python 3.6.7
root@docker-s-1vcpu-1gb-sfo2-01:~# python --version

Command 'python' not found, but can be installed with:

apt install python3
apt install python
apt install python-minimal

You also have python3 installed, you can run 'python3' instead.
```
Keep that fact in mind for later.

Before doing anything with Docker, first let's run a very simple Python Flask app:
```
root@docker-s-1vcpu-1gb-sfo2-01:~# cd docker-basics/basic-demo/
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# ls
Dockerfile  app.py
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# cat app.py
"""Demo Flask app."""
import sys
import platform
import logging
from argparse import ArgumentParser
from flask import Flask, jsonify

app = Flask(__name__)

# limit logging to errors only
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route("/")
def index():
    """Returns values of platform (OS), Python version, and the value of
    a string passed in at runtime to be the value of 'color'."""
    return jsonify({
        "platform": platform.platform(),
        "python_version": sys.version,
        "color": app.config['color']
    })


if __name__ == "__main__":

    # the app takes in a string as command line arg "color"
    parser = ArgumentParser()
    parser.add_argument('color')
    args = parser.parse_args()

    # set the passed-in string as the value of "color" in the app's config
    app.config['color'] = args.color

    # run the Flask app
    app.run(host='0.0.0.0')
```

The app is simple-- when you GET from its one route, it returns three (3) values:

* `platform.platform()`, which describes the host operating system

* `sys.version`, which is the version of Python that is running the app

* `color`, which is the value of a string passed in at run time (just so that multiple running copies of the app can be distinguished from each other).


Run the app using the Python 3 executable available on the host machine, passing in the string "blue" for the value of argument `color`:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# python3 app.py blue &
[1] 19444
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo#  * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: Do not use the development server in a production environment.
   Use a production WSGI server instead.
 * Debug mode: off
```
Ignore the warning, it's not an issue for this demo. Momentarily end the SSH session and start a new one (not required, it just makes the output of the `ps` command below a little clearer):
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# exit
logout
Connection to 178.128.11.142 closed.
$ ssh root@178.128.11.142
root@docker-s-1vcpu-1gb-sfo2-01:~# cd docker-basics/basic-demo/
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo#
```

Flask apps default to running on port 5000. To reach the running app, curl that port number on localhost:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# curl -s localhost:5000 | jq
{
  "color": "blue",
  "platform": "Linux-4.15.0-45-generic-x86_64-with-Ubuntu-18.04-bionic",
  "python_version": "3.6.7 (default, Oct 22 2018, 11:32:17) \n[GCC 8.2.0]"
}
```
Yes, that's correct: The app is being run on Ubuntu linux, and the app is being run by Python version 3.

Show the running processes on this machine with `ps -ef`. Add the `--forest` flag to show more clearly which processes are children of other processes:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# ps -ef --forest
UID        PID  PPID  C STIME TTY          TIME CMD
...
root       833     1  0 21:29 ?        00:00:00 /usr/bin/dockerd -H fd://
...
root       876     1  0 21:29 ?        00:00:06 /usr/bin/containerd
root       884     1  0 21:29 ?        00:00:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
...
root      1058     1  0 21:29 ?        00:00:00 /usr/sbin/sshd -D
root     19447  1058  0 21:57 ?        00:00:00  \_ sshd: root@pts/0
root     19516 19447  0 21:57 pts/0    00:00:00      \_ -bash
root     19535 19516  0 22:00 pts/0    00:00:00          \_ ps -ef --forest
root      1408     1  0 21:29 ?        00:00:00 /lib/systemd/systemd --user
root      1410  1408  0 21:29 ?        00:00:00  \_ (sd-pam)
root     19444     1  0 21:56 ?        00:00:00 python3 app.py blue
```
Three things to note:

* One of the processes is the running app, it has PID 19444.

* There is the expected Docker daemon process `dockerd`, it has PID 833.

* There is also the process `containerd`, with PID 876. It is the container runtime which [Docker works with](https://blog.docker.com/2017/08/what-is-containerd-runtime/) to run the containers.


Now let's run the same application, but this time inside a Docker container. So far, there are no Docker images on this machine. Confirm by running the [docker images](https://docs.docker.com/engine/reference/commandline/images/) command:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
```

In this same directory as the application code file `app.py` is another file called `Dockerfile`:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# cat Dockerfile
FROM centos:7

RUN yum -y upgrade && yum clean all \
    && yum -y install epel-release \
    && yum -y install python-pip vim jq

RUN pip install Flask

ADD app.py /app/app.py

WORKDIR /app

USER nobody
```
In particular, note that this image is going to be built using as its base a CentOS version 7 image, which is a different linux distribution than Ubuntu linux. (For comparisons of these two distributions see [here](https://linuxconfig.org/centos-vs-ubuntu) or [here](https://www.hostinger.com/tutorials/centos-vs-ubuntu).)

Build the image, giving it the name `basic_demo`:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker build -t basic_demo .
. . .
Successfully built db91f02383a8
Successfully tagged basic_demo:latest
```

Now there are two Docker images on this VM, the base image pulled from Docker Hub and our image which is an additional 202MB of file layers on top of it:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
basic_demo          latest              db91f02383a8        10 seconds ago      404MB
centos              7                   9f38484d220f        8 days ago          202MB
```

Before proceeding further, this is the perfect point in time to see Docker's use of Linux's [union filesystem capability](https://docs.docker.com/engine/docker-overview/#union-file-systems) in action. The output of the `docker images` command might make it look like we have filled up 606MB of disk space. But that is deceptive because half of the `basic_demo` image size is the layers of the base `centos` image. Use [docker system df](https://docs.docker.com/engine/reference/commandline/system/), the Docker analogue of the linux command `df` ("disk free") to see the total disk space actually taken up by Docker images on this machine:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker system df
TYPE                TOTAL               ACTIVE              SIZE                RECLAIMABLE
Images              2                   0                   403.6MB             403.6MB (100%)
Containers          0                   0                   0B                  0B
Local Volumes       0                   0                   0B                  0B
Build Cache         0                   0                   0B                  0B
```
Indeed the total space taken up by both images is only the 404MB size of the second image, which fully contains the first image. That shows a union filesystem in action.

Now let's use [docker run](https://docs.docker.com/engine/reference/commandline/run/) to run a container off of our newly build `basic_demo` image. Give the container the name "demo_red" and pass in as the one required argument the string "red":
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker run --rm -d -p 5555:5000 --name demo_red basic_demo python app.py red
37fb8c6ce733d352bc0c97bb25a532dc318c3d8272cccb051d27fc7fc2d26792
```

To see that a container is indeed running now, use [docker ps](https://docs.docker.com/engine/reference/commandline/ps/). I generally always add the `-a` flag to show all containers including states other than running (such as stopped or dead containers):
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker ps -a
CONTAINER ID        IMAGE               COMMAND               CREATED             STATUS              PORTS                    NAMES
37fb8c6ce733        basic_demo          "python app.py red"   20 seconds ago      Up 19 seconds       0.0.0.0:5555->5000/tcp   demo_red
```

"Enter" the container by opening a bash shell on it with the [docker exec](https://docs.docker.com/engine/reference/commandline/exec/) command:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker exec -it demo_red bash
bash-4.2$
```
Note that the command prompt has changed. Where inside the container directory structure are we and what is found there?
```
bash-4.2$ pwd
/app
bash-4.2$ ls
app.py
```
We are down in the `/app` directory because of the `WORKDIR /app` command in the Dockerfile. In this directory is a copy of the `app.py` file because the `ADD app.py /app/app.py` command in the Dockerfile copied it in during the build process.

Inside the container, the environment behaves as if the CentOS distribution of linux is installed:
```
bash-4.2$ cat /etc/redhat-release
CentOS Linux release 7.6.1810 (Core)
```

While for many purposes one Linux distribution is just as good as another, distributions do differ in details. In particular, one difference between CentOS 7 vs Ubuntu 18.04 is that CentOS [only ships with Python version 2](https://linuxize.com/post/how-to-install-python-3-on-centos-7/):
```
bash-4.2$ python --version
Python 2.7.5
bash-4.2$ python3
bash: python3: command not found
```

The container was started with command "python app.py red". Therefore here inside the container, the app should be running on localhost port 5000. Test it:
```
bash-4.2$ curl -s localhost:5000 | jq
{
  "color": "red",
  "platform": "Linux-4.15.0-45-generic-x86_64-with-centos-7.6.1810-Core",
  "python_version": "2.7.5 (default, Oct 30 2018, 23:45:53) \n[GCC 4.8.5 20150623 (Red Hat 4.8.5-36)]"
}
```
**Note carefully the different output.** As far as ***this*** running app is concerned, it is running on CentOS and it is being run with Python 2, *not* Python 3. Now, this particular app is so simple that it works exactly the same in Python 2 or 3. But imagine if it was a legacy app built and run on Python 2 which will break if run with Python 3. Or imagine if it was an app which relied on some functionality built into CentOS which does not work the same way in Ubuntu. With containerization, we are able to give an app a desired OS without having to create a separate second VM and do a full guest OS installation into it.

One key benefit of containers is **isolation**. From inside the container, there is no access to the host VM's file system. For example, try to find one of the files in the directory cloned from github such as the `Dockerfile` by doing `find / -name "Dockerfile"`. You cannot find that file anywhere inside the container. The container's file system is isolated from the host file system.

Another way to see the isolation the container provides is to view all running processes with the same `ps -ef --forest` command run earlier out on the host:
```
bash-4.2$ ps -ef --forest
UID        PID  PPID  C STIME TTY          TIME CMD
nobody      36     0  0 23:08 pts/0    00:00:00 bash
nobody      58    36  0 23:20 pts/0    00:00:00  \_ ps -ef --forest
nobody       1     0  0 22:16 ?        00:00:00 python app.py red
```
Note that the running app (`python app.py red`) has PID **1**. Where is the process for the still-running *blue* copy of the app? Not anywhere that the environment inside this container knows about.

Now exit the container shell (the container continues to run) and contrast that to what processes are running on the *host*. Do the same `ps -ef --forest` command:
```
bash-4.2$ exit
exit
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# ps -ef --forest
UID        PID  PPID  C STIME TTY          TIME CMD
...
root       833     1  0 21:29 ?        00:00:08 /usr/bin/dockerd -H fd://
root     20294   833  0 22:16 ?        00:00:00  \_ /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 5555 -container-ip 172.17.0.2 -container-port 5000
...
root       876     1  0 21:29 ?        00:00:22 /usr/bin/containerd
root     20300   876  0 22:16 ?        00:00:01  \_ containerd-shim -namespace moby -workdir /var/lib/containerd/io.containerd.runtime.v1.linux/moby/37fb8c6ce733d352bc0c97bb25a53
99       20328 20300  0 22:16 ?        00:00:01      \_ python app.py red
...
root     19444     1  0 21:56 ?        00:00:00 python3 app.py blue
```
Aha! In addition to process `python3 app.py blue` which we left running from before, now we see on the host there is also running a distinct process `python app.py red`, which is the process running inside the container. What from inside the container appeared to be a process with PID 1 turns out in truth to be a process with PID 20328 on the host. Also, the tree structure shows that the red copy of the application is running as a child of `containerd`, in a [namespace](https://docs.docker.com/engine/docker-overview/#namespaces) of its own.

Containers would not be very convenient if in order to reach the apps running inside the container we had to always open an interactive shell to "step inside" the container. To reach the app from the host environment (ultimately even remotely from another machine, but skip that for now), we reach it on the port number which was mapped to port 5000 inside the container.

Earlier when we started the container, I made sure to pick a host machine port number other than 5000 because that port is already in use by the "blue" copy of the app. I mapped the alternate port number (5555) to port 5000 inside the container:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker ps -a
CONTAINER ID        IMAGE               COMMAND               CREATED             STATUS              PORTS                    NAMES
37fb8c6ce733        basic_demo          "python app.py red"   About an hour ago   Up About an hour    0.0.0.0:5555->5000/tcp   demo_red
```
Note the `PORTS` column. This says that a GET request to port 5555 on the *host* machine will be forwarded to port 5000 on the *container*. So we can reach the app inside the container as long as from out here on the host we curl port 5555 instead:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# curl -s localhost:5555 | jq
{
  "color": "red",
  "platform": "Linux-4.15.0-45-generic-x86_64-with-centos-7.6.1810-Core",
  "python_version": "2.7.5 (default, Oct 30 2018, 23:45:53) \n[GCC 4.8.5 20150623 (Red Hat 4.8.5-36)]"
}
```
That is *exactly* the same output we got from the red copy of the app when we hit its endpoint while standing inside the container. The red app is telling *its version of the truth*: as far as the app knows, it is being run with Python version 2, and it is running on the CentOS distribution of linux. It has no idea that in fact the OS kernel is really Ubuntu linux, not CentOS. *It is not aware of its containerized state.* Indeed, it does not know we are reaching via host machine port 5555-- as far as the app knows, the GET request came in on localhost:5000.

Let's run two more containers, each with a different color and a distinct port number mapping:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker run --rm -d -p 6666:5000 --name demo_green basic_demo python app.py green
bf19e3072409380e0e384d9de8a618314888123db5cf4a4fde624b675beaff01
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker run --rm -d -p 7777:5000 --name demo_yellow basic_demo python app.py yellow
11c08b5a87bef586a848adb2ec211601c1e44de47d96445546db4bf113a3ffce
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo#
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
11c08b5a87be        basic_demo          "python app.py yellow"   9 seconds ago       Up 8 seconds        0.0.0.0:7777->5000/tcp   demo_yellow
bf19e3072409        basic_demo          "python app.py green"    33 seconds ago      Up 32 seconds       0.0.0.0:6666->5000/tcp   demo_green
37fb8c6ce733        basic_demo          "python app.py red"      About an hour ago   Up About an hour    0.0.0.0:5555->5000/tcp   demo_red
```

Each of the applications runs on port 5000 in its own CentOS 7 environment, blissfully unaware of the others. If we go into the green or yellow containers, we'd see exactly the same thing we saw in the red container-- that PID 1 inside the container is the application running on port 5000. From out on the host we can reach all of them:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# for p in 5555 6666 7777; do curl -s localhost:$p | jq ; done
{
  "color": "red",
  "platform": "Linux-4.15.0-45-generic-x86_64-with-centos-7.6.1810-Core",
  "python_version": "2.7.5 (default, Oct 30 2018, 23:45:53) \n[GCC 4.8.5 20150623 (Red Hat 4.8.5-36)]"
}
{
  "color": "green",
  "platform": "Linux-4.15.0-45-generic-x86_64-with-centos-7.6.1810-Core",
  "python_version": "2.7.5 (default, Oct 30 2018, 23:45:53) \n[GCC 4.8.5 20150623 (Red Hat 4.8.5-36)]"
}
{
  "color": "yellow",
  "platform": "Linux-4.15.0-45-generic-x86_64-with-centos-7.6.1810-Core",
  "python_version": "2.7.5 (default, Oct 30 2018, 23:45:53) \n[GCC 4.8.5 20150623 (Red Hat 4.8.5-36)]"
}
```

And we can see that the red, green and yellow apps run as separate children of the `containerd` process:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# ps -ef --forest
UID        PID  PPID  C STIME TTY          TIME CMD
...
root       853     1  0 Mar04 ?        00:00:43 /usr/bin/dockerd -H fd://
root       833     1  0 21:29 ?        00:00:08 /usr/bin/dockerd -H fd://
root     20294   833  0 22:16 ?        00:00:00  \_ /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 5555 -container-ip 172.17.0.2 -container-port 5000
root     20719   833  0 23:34 ?        00:00:00  \_ /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 6666 -container-ip 172.17.0.3 -container-port 5000
root     20820   833  0 23:35 ?        00:00:00  \_ /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 7777 -container-ip 172.17.0.4 -container-port 5000
...
root       876     1  0 21:29 ?        00:00:25 /usr/bin/containerd
root     20300   876  0 22:16 ?        00:00:01  \_ containerd-shim -namespace moby -workdir /var/lib/containerd/io.containerd.runtime.v1.linux/moby/37fb8c6ce733d352bc0c97bb25a53
99       20328 20300  0 22:16 ?        00:00:01  |   \_ python app.py red
root     20725   876  0 23:34 ?        00:00:00  \_ containerd-shim -namespace moby -workdir /var/lib/containerd/io.containerd.runtime.v1.linux/moby/bf19e3072409380e0e384d9de8a61
99       20751 20725  0 23:34 ?        00:00:00  |   \_ python app.py green
root     20827   876  0 23:35 ?        00:00:00  \_ containerd-shim -namespace moby -workdir /var/lib/containerd/io.containerd.runtime.v1.linux/moby/11c08b5a87bef586a848adb2ec211
99       20855 20827  0 23:35 ?        00:00:00      \_ python app.py yellow
...
root     19444     1  0 21:56 ?        00:00:01 python3 app.py blue
```

This concludes the basic demo. To clean up, you can stop and remove all running containers at once with [docker stop](https://docs.docker.com/engine/reference/commandline/stop/). You can stop them one at a time by name; a convenient way to stop all at once is:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker stop $(docker ps -a -q)
11c08b5a87be
bf19e3072409
37fb8c6ce733
```
Strictly speaking, `docker stop` only stops a container but does not actually remove it. (Removing it means deleting its read-write file layer). A stopped container can be re-started. However, in my `docker run` commands I purposely included the `--rm` flag so that when the containers are stopped they are automatically removed (deleted) as well, saving me having to follow up `docker stop` with [docker rm](https://docs.docker.com/engine/reference/commandline/rm/) commands.

We can also remove the images with [docker rmi](https://docs.docker.com/engine/reference/commandline/rmi/):
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker rmi -f $(docker images -q)
```

The VM is now back to a "pristine" Docker state:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/basic-demo# docker system df
TYPE                TOTAL               ACTIVE              SIZE                RECLAIMABLE
Images              0                   0                   0B                  0B
Containers          0                   0                   0B                  0B
Local Volumes       0                   0                   0B                  0B
Build Cache         0                   0                   0B                  0B
```
