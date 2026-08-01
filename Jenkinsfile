pipeline {

    agent any

    environment {

        BACKEND_IMAGE = "devaraj74/employee-management-backend"
        FRONTEND_IMAGE = "devaraj74/employee-management-frontend"

        SONAR_TOKEN = credentials('sonarqube-token')
    }


    stages {


        stage('Build Application') {

            steps {

                sh '''
                echo "Installing backend dependencies"

                cd backend
                pip3 install -r requirements.txt

                echo "Checking frontend files"

                cd ../frontend
                ls -la
                '''
            }
        }



        stage('SonarQube Analysis') {

            steps {

                withSonarQubeEnv('sonarqube') {

                    sh '''
                    sonar-scanner \
                    -Dsonar.projectKey=employee-management \
                    -Dsonar.sources=. \
                    -Dsonar.host.url=http://172.31.35.57:9000 \
                    -Dsonar.login=$SONAR_TOKEN
                    '''
                }
            }
        }



        stage('Docker Build') {

            steps {

                sh '''

                echo "Building Backend Docker Image"

                docker build \
                -t $BACKEND_IMAGE:$BUILD_NUMBER \
                ./backend



                echo "Building Frontend Docker Image"

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

                    echo "Logging into DockerHub"

                    docker login \
                    -u $DOCKER_USERNAME \
                    -p $DOCKER_PASSWORD



                    echo "Pushing Backend Image"

                    docker push \
                    $BACKEND_IMAGE:$BUILD_NUMBER



                    echo "Pushing Frontend Image"

                    docker push \
                    $FRONTEND_IMAGE:$BUILD_NUMBER


                    '''
                }
            }
        }





        stage('Deploy to Kubernetes') {

            steps {

                sh '''

                echo "Applying Kubernetes manifests"

                kubectl apply -f kubernetes/



                echo "Updating Backend Deployment"

                kubectl set image deployment/backend \
                backend=$BACKEND_IMAGE:$BUILD_NUMBER \
                -n employee-management



                echo "Updating Frontend Deployment"

                kubectl set image deployment/frontend \
                frontend=$FRONTEND_IMAGE:$BUILD_NUMBER \
                -n employee-management



                echo "Checking rollout status"

                kubectl rollout status deployment/backend \
                -n employee-management



                kubectl rollout status deployment/frontend \
                -n employee-management

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
