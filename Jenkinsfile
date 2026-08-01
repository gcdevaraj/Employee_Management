pipeline {

    agent any


    environment {

        BACKEND_IMAGE = "devaraj74/employee-management-backend"
        FRONTEND_IMAGE = "devaraj74/employee-management-frontend"

        KUBECONFIG = "/var/lib/jenkins/.kube/config"

        SONAR_TOKEN = credentials('sonarqube-token')
    }



    stages {


        stage('Build Application') {

            steps {

                sh '''
                
                echo "Checking backend"

                ls -la backend

                echo "Checking frontend"

                ls -la frontend

                '''
            }
        }




        stage('SonarQube Analysis') {

            steps {

                withSonarQubeEnv('sonarqube') {

                    sh '''

                    sonar-scanner \
                    -Dsonar.projectKey=employee-management \
                    -Dsonar.sources=backend \
                    -Dsonar.host.url=http://172.31.35.57:9000 \
                    -Dsonar.login=$SONAR_TOKEN

                    '''
                }
            }
        }





        stage('Docker Build') {

            steps {

                sh '''

                echo "Building Backend Image"

                docker build \
                -t $BACKEND_IMAGE:$BUILD_NUMBER \
                ./backend



                echo "Building Frontend Image"

                docker build \
                -t $FRONTEND_IMAGE:$BUILD_NUMBER \
                ./frontend


                '''
            }
        }





        stage('Docker Login & Push') {

            steps {


                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub',
                    usernameVariable: 'DOCKER_USERNAME',
                    passwordVariable: 'DOCKER_PASSWORD'
                )]) {


                    sh '''

                    echo "Login to Docker Hub"


                    echo $DOCKER_PASSWORD | docker login \
                    -u $DOCKER_USERNAME \
                    --password-stdin



                    echo "Pushing Backend"

                    docker push \
                    $BACKEND_IMAGE:$BUILD_NUMBER



                    echo "Pushing Frontend"

                    docker push \
                    $FRONTEND_IMAGE:$BUILD_NUMBER


                    '''
                }
            }
        }





        stage('Deploy to Kubernetes') {


            steps {


                sh '''

                echo "Deploying Kubernetes resources"


                export KUBECONFIG=/var/lib/jenkins/.kube/config



                kubectl apply -f kubernetes/namespace.yaml


                kubectl apply -f kubernetes/



                echo "Updating backend image"


                kubectl set image deployment/backend \
                backend=$BACKEND_IMAGE:$BUILD_NUMBER \
                -n employee-management



                echo "Updating frontend image"


                kubectl set image deployment/frontend \
                frontend=$FRONTEND_IMAGE:$BUILD_NUMBER \
                -n employee-management




                echo "Waiting for backend rollout"


                kubectl rollout status deployment/backend \
                -n employee-management \
                --timeout=120s




                echo "Waiting for frontend rollout"


                kubectl rollout status deployment/frontend \
                -n employee-management \
                --timeout=120s




                echo "Final Status"


                kubectl get pods -n employee-management


                '''
            }
        }

    }



    post {


        success {

            echo "CI/CD Pipeline completed successfully"

        }


        failure {

            echo "Pipeline failed"

        }

    }

}
