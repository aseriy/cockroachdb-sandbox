# cockroachdb-sandbox

https://podman-desktop.io/docs/containers/registries

https://podman-desktop.io/docs/compose/running-compose#:~:text=With%20Podman%20Desktop%2C%20you%20can,defined%20in%20a%20Compose%20file.


``` bash
podman compose --file docker-compose.yml up --detach
```



On AWS:

https://docs.docker.com/engine/install/ubuntu/

```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```


```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

https://stackoverflow.com/questions/48957195/how-to-fix-docker-got-permission-denied-issue

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
docker run hello-world
reboot
```


Build Docker image for HSProxy:

```bash
docker build -f Dockerfile.haproxy -t roach-haproxy .
```

Docker Compose Install

```bash
sudo apt-get install docker-compose-plugin
docker compose version
```


Start

```bash
docker compose -f docker-compose.yml up --detach
```


Net tools aren't installed by default:

```bash
sudo apt install net-tools
```

