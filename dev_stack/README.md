# Cloud Local Stack
LocalStack is a fully functional local AWS cloud stack. It allows you to test and develop your cloud applications locally.



## Tools
- Ngrok
- Auth0
- GitHub App
- Modal
- AWS-CDK

## Ngrok
ngrok is a tool that creates a secure tunnel to your localhost, allowing you to expose your local server to the internet. This is useful for testing webhooks, APIs, and other services that require a public URL.
Tunnels
- webapp tunnel -> webapp frontend
- api tunnel -> api backend
- tcp tunnel -> local postgres db
### Installation
```bash
brew install ngrok
```

## Auth0
Auth0 is an authentication and authorization platform that provides a secure way to manage user identities and access control. It allows you to implement authentication in your applications using various methods, including social logins, username/password, and passwordless authentication.


## GitHub App

GitHub Apps are a way to integrate with GitHub and automate workflows. They can be used to perform actions on behalf of users, such as creating issues, commenting on pull requests, and more. GitHub Apps can be installed on organizations and repositories, and they have granular permissions to access only the data they need.


## Modal
Modal is a cloud-based platform that allows you to run Python code in the cloud. It provides a simple way to run scripts, build APIs, and create web applications without worrying about infrastructure. Modal supports various libraries and frameworks, making it easy to deploy your code and scale it as needed.


## AWS-CDK
The AWS Cloud Development Kit (CDK) is an open-source software development framework that allows you to define cloud infrastructure using familiar programming languages. It enables you to model and provision AWS resources using code, making it easier to manage and deploy your cloud applications.
