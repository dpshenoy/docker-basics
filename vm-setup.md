The VM used in the demos is a Digital Ocean droplet (the cheapest $5/month option). Specifically, the Ubuntu linux version with Docker pre-installed: https://cloud.digitalocean.com/marketplace/5ba19751fc53b8179c7a0071?i=12033b&referrer=droplets%2Fnew

No additional configuration is needed for the parts of the demos which run in Docker.

For the first few steps of the basic demo where the app is run directly on the VM (not inside Docker) I did a few prelimary setup steps:

Update the linux packages list:
```
root@docker-s-1vcpu-1gb-sfo2-01:~# apt update
```

Install `tree` (optional; it's nice to have for viewing the cloned github repo directory's structure):
```
root@docker-s-1vcpu-1gb-sfo2-01:~# apt install tree
```

Install `pip` (for python3)
```
root@docker-s-1vcpu-1gb-sfo2-01:~# apt install python3-pip
```

Use pip to install the [Flask](http://flask.pocoo.org/) package:
```
root@docker-s-1vcpu-1gb-sfo2-01:~# pip3 install Flask
```
