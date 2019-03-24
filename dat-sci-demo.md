These steps demonstrate how different versions of a trained model can be containerized. This is intended as a simple example and is not the only (or best) way to do this for use in production. (In particular, there is duplication of code in the two subdirectories for the two models. That is on purpose since the goal here is to keep the example simple to follow, even if not efficient.)

Directory `dat-sci-demo/` contains a Jupyter notebook and two subdirectories:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics# tree dat-sci-demo/
dat-sci-demo/
├── lin_svc
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── trained_classifier.pkl
├── pickle_models.ipynb
└── svc
    ├── Dockerfile
    ├── app.py
    ├── requirements.txt
    └── trained_classifier.pkl

2 directories, 9 files
```

The Jupyter notebook `pickle_models.ipynb` runs a simplified version of [a Scikit-learn example](https://scikit-learn.org/stable/auto_examples/svm/plot_iris.html). That example compares the performance of two support vector machine classifiers on the iris data set. The notebook has already been run to completion. It trained the two classifiers and it saved each as a `.pkl` file in the two subdirectories. The classifiers take in values for an iris' sepal length and sepal width and use them to predict whether the species is "setosa", "virginica" or "versicolor".

The subdirectory `svc` received a trained model made using `sklearn.svm.SVC` with a linear kernel.

The subdirectory `lin_svc` received a trained model made using `sklearn.svm.LinearSVC`, which is slightly different. See the plot in the Jupyter notebook. In particular, note the test point (a large black "X" near the center) at which the two models predict different species.

The rest of the files in each subdirectory (`Dockerfile`, `app.py`, `requirements.txt`) are identical. (I generally aim to keep things DRY, but for this demo I wanted separate subdirs for clarity and comparison.)

The app is a Python Flask app similar to the one in the basic demo. At run time the app loads the `trained_classifier.pkl` file, which the `Dockerfile` builds into the image. This method enables the same application code to run any number of different models; you can just swap out the `.pkl` file and rebuild.

Build an image for each of these two different versions of the app. **Note:** both images will be called "iris". To distinguish the images I will use different [tags](https://docs.docker.com/glossary/?term=tag). Tags are the recommended way to version images.

The `docker build` command can be issued from the directory level above the two subdirectories, as long as the relative path to the `Dockerfile` down in each one is properly specified:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# pwd
/root/docker-basics/dat-sci-demo
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# ls -1F
lin_svc/
pickle_models.ipynb
svc/
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# docker build -t iris:svc ./svc/
. . .
Successfully built 1920e0e5551c
Successfully tagged iris:svc
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# docker build -t iris:lin_svc ./lin_svc/
Successfully built 21fdb7491e72
Successfully tagged iris:lin_svc
```

Most of the file system layers are identical, which is why the second build goes so quickly. We have two distinct images now:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED              SIZE
iris                lin_svc             21fdb7491e72        51 seconds ago       378MB
iris                svc                 1920e0e5551c        About a minute ago   378MB
...
```

Run a container off each image. Inside each container the app will run on port 5000, the default port number used by Flask. Map host VM port number 5001 to container port 5000 for the `svc` model version of the app. Map host VM port number 5002 to container port 5000 for the `lin_svc` model version of the app. This way we can run both versions at the same time and compare their predictions for the test point:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# docker run --rm -d -p 5001:5000 --name iris_svc iris:svc
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# docker run --rm -d -p 5002:5000 --name iris_lin_svc iris:lin_svc
```

Both versions are running:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# docker ps -a
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS                    NAMES
7ae1f9e80bbb        iris:lin_svc        "python app.py"     9 seconds ago       Up 7 seconds        0.0.0.0:5002->5000/tcp   iris_lin_svc
86d439345763        iris:svc            "python app.py"     40 seconds ago      Up 39 seconds       0.0.0.0:5001->5000/tcp   iris_svc
```

Per the Jupyter notebook, the test point is an iris with **sepal length == 5.8** and **sepal width == 3.4**. The app takes in these values as query string params called "length" and "width".

Get a prediction from the `svc` model (note the escaping backslashes preceeding characters `?`, `=`, and `&`):
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# curl -s http://localhost:5001\?length\=5.8\&width\=3.4 | jq
{
  "predicted_class": "versicolor",
  "sepal_length": 5.8,
  "sepal_width": 3.4
}
```
The `svc` model predicts the test flower's species is **versicolor**.

Compare that to a prediction from the `lin_svc` model for the same test point:
```
root@docker-s-1vcpu-1gb-sfo2-01:~/docker-basics/dat-sci-demo# curl -s http://localhost:5002\?length\=5.8\&width\=3.4 | jq
{
  "predicted_class": "setosa",
  "sepal_length": 5.8,
  "sepal_width": 3.4
}
```
In contrast, the `lin_svc` model predicts the test flower's species is **setosa**.

As this very simple demo illustrates, using Docker containers it is easy to simultaneously deploy different versions of a model. You could run both at the same time and (using additional methods not discussed here) direct a certain percentage of traffic to one container and the rest to the other container, and then gather data on the results of running each model.

Or, pretend the `svc` model was "good enough" for my users yesterday. Today the `lin_svc` model became available. I want to switch my users to getting the new better predictions from the `lin_svc` model. Because my users are so relentlessly demanding, I need to bring the new model online with zero down time. Depending on my production environment (I'm thinking Kubernetes here, which is how I would do this), I would start running several `lin_svc` containers running and then redirect all traffic to them, after which I can safely remove the `svc` containers.
