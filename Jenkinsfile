pipeline {
    agent any

    parameters {
        choice(
            name: 'DEPLOY_STRATEGY',
            choices: ['rolling', 'blue-green', 'canary', 'shadow', 'ab', 'rollback'],
            description: 'Deployment strategy to apply on the cluster'
        )
        string(
            name: 'IMAGE_REPO',
            defaultValue: 'usernamejaya/aceest-fitness',
            description: 'Docker Hub repository, without a tag'
        )
        string(
            name: 'APP_VERSION',
            defaultValue: '3.2.4',
            description: 'Image tag to build and push'
        )
    }

    environment {
        IMAGE_REPO = "${params.IMAGE_REPO}"
        APP_VERSION = "${params.APP_VERSION}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh 'python3 -m pip install -r requirements-dev.txt'
                sh 'python3 -m pytest --junitxml=test-results.xml'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'sonar-scanner'
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build and Push Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker build --build-arg APP_VERSION="$APP_VERSION" -t "$IMAGE_REPO:$APP_VERSION" .
                        docker push "$IMAGE_REPO:$APP_VERSION"
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                sh 'kubectl apply -f k8s/namespace.yaml'
                script {
                    if (params.DEPLOY_STRATEGY == 'rolling') {
                        sh 'kubectl apply -f k8s/rolling/'
                        sh 'kubectl rollout status deployment/aceest-rolling -n aceest --timeout=180s'
                    } else if (params.DEPLOY_STRATEGY == 'blue-green') {
                        sh 'kubectl apply -f k8s/blue-green/'
                        sh 'kubectl rollout status deployment/aceest-blue -n aceest --timeout=180s'
                        sh 'kubectl rollout status deployment/aceest-green -n aceest --timeout=180s'
                    } else if (params.DEPLOY_STRATEGY == 'canary') {
                        sh 'kubectl apply -f k8s/canary/'
                        sh 'kubectl rollout status deployment/aceest-stable -n aceest --timeout=180s'
                        sh 'kubectl rollout status deployment/aceest-canary -n aceest --timeout=180s'
                    } else if (params.DEPLOY_STRATEGY == 'shadow') {
                        sh 'kubectl apply -f k8s/shadow/primary.yaml'
                        sh 'kubectl apply -f k8s/shadow/shadow.yaml'
                        sh 'kubectl rollout status deployment/aceest-primary -n aceest --timeout=180s'
                        sh 'kubectl rollout status deployment/aceest-shadow -n aceest --timeout=180s'
                    } else if (params.DEPLOY_STRATEGY == 'ab') {
                        sh 'kubectl apply -f k8s/ab/'
                        sh 'kubectl rollout status deployment/aceest-a -n aceest --timeout=180s'
                        sh 'kubectl rollout status deployment/aceest-b -n aceest --timeout=180s'
                        sh 'kubectl rollout status deployment/aceest-ab-router -n aceest --timeout=180s'
                    } else if (params.DEPLOY_STRATEGY == 'rollback') {
                        sh 'kubectl apply -f k8s/rollback/deployment.yaml'
                        sh 'kubectl rollout status deployment/aceest-rolling -n aceest --timeout=180s'
                    }
                }
            }
        }

        stage('Smoke Test') {
            steps {
                script {
                    def deployment = 'aceest-rolling'
                    if (params.DEPLOY_STRATEGY == 'blue-green') {
                        deployment = 'aceest-blue'
                    } else if (params.DEPLOY_STRATEGY == 'canary') {
                        deployment = 'aceest-stable'
                    } else if (params.DEPLOY_STRATEGY == 'shadow') {
                        deployment = 'aceest-primary'
                    } else if (params.DEPLOY_STRATEGY == 'ab') {
                        deployment = 'aceest-a'
                    }
                    sh "kubectl exec -n aceest deploy/${deployment} -- python -c \"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/health').read())\""
                }
            }
        }
    }

    post {
        failure {
            sh 'kubectl rollout undo deployment/aceest-rolling -n aceest || true'
        }
        always {
            junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
    }
}
