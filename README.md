# kubernetes-workshop

## Prerequisites
#### AWS Command Line Interface
[AWS official documentation](https://aws.amazon.com/cli/)

* Install
With Python pip: ```pip install awscli```
With brew (OS X only): ```brew install awscli```

* Set up your AWS credentials and default region:
```
export AWS_ACCESS_KEY_ID=<access key>
export AWS_SECRET_ACCESS_KEY=<secret access key>
export AWS_DEFAULT_REGION=eu-central-1
```

* Test that everything works
Run the command ```aws ec2 describe-instances```, and make sure it does not give any error about keys or region.

#### Get Kubernetes
You need about 3.5GB of free space for Kubernetes; 1.5GB to download, and 1.9GB after unpacking the file.
```
curl -O https://storage.googleapis.com/kubernetes-release/release/v1.3.7/kubernetes.tar.gz
tar -xzf kubernetes.tar.gz
```
Then you need to patch a [broken file](https://github.com/kubernetes/kubernetes/issues/30495)
```
cd kubernetes
curl -O https://raw.githubusercontent.com/bardoo/kubernetes-workshop/master/fix-cluster-common.patch
patch -p0 < fix-cluster-common.patch
```

#### Get kubectl (Command line administration tool)
Install with brew: ```brew install kubectl```, or add to your PATH, as described in the [official documentation](kubernetes.io/docs/getting-started-guides/aws/#command-line-administration-tool-kubectl):
```
# OS X
export PATH=<path/to/kubernetes-directory>/platforms/darwin/amd64:$PATH

# Linux
export PATH=<path/to/kubernetes-directory>/platforms/linux/amd64:$PATH
```

## 1. Set up kubernetes cluster
### 1.1 Config
```
export KUBERNETES_PROVIDER=aws
export KUBE_AWS_ZONE=eu-central-1a
export NUM_NODES=2
export MASTER_SIZE=t2.micro
export NODE_SIZE=t2.micro
export AWS_S3_REGION=eu-central-1
export AWS_S3_BUCKET=k8s-ws-kubernetes-artifacts
export KUBE_AWS_INSTANCE_PREFIX=k8s-<dittnavn>
```
Do not change the AWS_S3_REGION or AWS_S3_BUCKET settings, as we have pre-uploaded the Kubernetes files to them.
### 1.2 Launch the environment
```
cd kubernetes
./cluster/kube-up.sh
```
This command will launch the entire environment for you (vpc, nodes, security groups, elastic ip, autoscaling, etc.), upload everything that is needed by Kubernetes to a S3 bucket (unless already uploaded), and install the Kubernetes software on the master and slave nodes.

When the command is finished, it will give you the Elastic IP for the master node, along with endpoints of some services that are set up. This info can later be retrieved by running ```kubectl cluster-info```.
### 1.3 Explore it
The services uses basic auth and you find the credentials by running ```kubectl config view```. They are also using SSL/TLS, so you must access the certificate. 

Some interesting services:

| Service |  URL |
| --------| ---- |
| Kubernetes Dashboard | `https://<master-ip\>api/v1/proxy/namespaces/kube-system/services/kubernetes-dashboard` |
| Kibana |  `https://<master-ip>/api/v1/proxy/namespaces/kube-system/services/kibana-logging` |
| Grafana | `https://<master-ip>/api/v1/proxy/namespaces/kube-system/services/monitoring-grafana`|

## 2. Deploy application
### 2.1 Run application
```
kubectl run kubernetes-workshop --image=815899840094.dkr.ecr.eu-central-1.amazonaws.com/kubernetes-workshop:v1 --port=5000
```
This will create a *deployment* named *kubernetes-workshop*, in which a *pod* is created. In this pod, the Docker image located at the ECR address 815899... is run, exposing port 5000.

### 2.2 Explore the CLI
The two basic commands to show information about the resources are ```kubectl get <resource>``` and ```kubectl describe <resource>```. The get command gives some short information about the resource, while the describe command shows very detailed information.
To only show information about a specific resource (if you have multiple of the same type), you can add the name of it to the commands (```kubectl describe <resource> <resource-name>```).

Check events for the entire cluster
```
kubectl get events
```

Info about running nodes (minions, actual AWS instances)
```
kubectl get nodes
```

Detailed info about a node (use node-name from previous command)
```
kubectl describe nodes <node-name>
```

Check status of your deploy
```
kubectl get deployments
```

Check pods
```
kubectl get pods
```

Check the system output of a pod (use pod name from ```kubectl get pods```
```
kubectl logs <full-pod-name>
```

### 2.3 Expose the application to the internet
```
kubectl expose deployment kubernetes-workshop --type="LoadBalancer" --port=80 --target-port=5000
```
This command will create a *service* for our application, by setting up an AWS load balancer, that listens on port 80 and connects to our application on port 5000.

To get info about all running services (should be the kubernetes master and our application).
```
kubectl get services
```
Since AWS uses very long DNS names, you will probably just see a part of it under the EXTERNAL-IP column. To get the full address, you can use the more verbose *describe* command. (It might take some minutes before the load balancer is set up and has an external IP).
```
kubectl describe services kubernetes-workshop
```

### 2.4 Set up multiple replicas
We are currently only running one instance of our application in the cluster. To scale that up to four, run
```
kubectl scale deployment kubernetes-workshop --replicas=4
```
This will launch new replicas of the deployment, by creating new pods, spread out in the cluster.

## 3. Release a new version of application
We have uploaded a second version of the app, that prints out v2 instead of v1, so you can see that it has been updated.
To update the application, you tell Kubernetes which deployment to update, and the new image to run in that deployment.
```
kubectl set image deployments/kubernetes-workshop kubernetes-workshop=815899840094.dkr.ecr.eu-central-1.amazonaws.com/kubernetes-workshop:v2
```

To check the status of the update
```
kubectl get rs
```
Here you see that it keeps some of the old replicas while creating the new ones.

For more details about the strategy and settings that are used for a roll out, you can check the detailed information of the deployment.
```
kubectl describe deployments kubernetes-workshop
```

## 5. Set up autoscaling

### 5.1 Autoscaling deployments
[Autoscaling](http://kubernetes.io/docs/user-guide/kubectl/kubectl_autoscale/) can be set up on a deployment.
```
kubectl autoscale deployment kubernetes-workshop --min=2 --max=6 --cpu-percent=60
```
The autoscaler will then control the number of pods that are running, depending on the CPU usage.

### 5.2 Scaling minions
Autoscaling is done by modifying the AWS autoscaling group. When a new node is created in the autoscaling group, it will automatically be configured and registered to the cluster.

## 6. Logging
Kubernetes has built in support for either Google Cloud Logging or the ELK stack (ElasticSearch, Logstash and Kibana).
When run on AWS, the latter alternative is set up automatically.

## 7. Destroy environment
This will take down the application and destroy the entire environment.
```
cd kubernetes
./cluster/kube-down.sh
```