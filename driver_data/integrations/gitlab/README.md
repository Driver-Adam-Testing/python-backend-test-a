
# GitLab-ee:17.3.5 Setup

1. mkdir -p ~/.gitlab-docker
2. export GITLAB_HOME=~/.gitlab-docker
3. Open`docker-compose.yml` and set `GITLAB_ROOT_PASSWORD` to your desired password
4. Run`docker-compose up -d`
5. Once Container `gitlab` has started open $GITLAB_HOME/config/gitlab.rb
6. Search for external_url and replace with your domain (e.g. external_url 'https://your-domain.ngrok.io/')
    ```
    external_url 'http://your-domain.ngrok.io'

    # Disable Let’s Encrypt
    letsencrypt['enable'] = false
    nginx['redirect_http_to_https'] = false
    ```
7. Save and exit
8. In your terminal run `docker exec -it gitlab /bin/sh`then `gitlab-ctl reconfigure`
9. if you are using ngrok run `ngrok http --url=your-domain.ngrok.io 80`
10. Open your browser and navigate to `http://your-domain.ngrok.io` and login with `root` and the password you set in step 3



## GitLab-ee:17.3.5 Docs
https://archives.docs.gitlab.com/17.3/ee/api/rest/index.html
