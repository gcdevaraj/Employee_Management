pipeline {

    agent any

    environment {
        DOCKER_IMAGE = "devaraj74/employee-management-backend"
        SONAR_TOKEN = credentials('sonarqube-token')
    }


    stages {


        


        stage('Build Application') {
            steps {

                sh '''
                cd backend
                mvn clean package -DskipTests
                '''

            }
        }


        stage('SonarQube Analysis') {

            steps {

                withSonarQubeEnv('sonarqube') {

                    sh '''
                    cd backend

                    mvn sonar:sonar \
                    -Dsonar.projectKey=employee-management \
                    -Dsonar.host.url=http://3.109.49.84:9000 \
                    -Dsonar.login=$SONAR_TOKEN

                    '''

                }

            }

        }



        stage('Docker Build') {

            steps {

                sh '''

                docker build \
                -t $DOCKER_IMAGE:$BUILD_NUMBER \
                ./backend

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

                    docker login \
                    -u $DOCKER_USERNAME \
                    -p $DOCKER_PASSWORD


                    docker push \
                    $DOCKER_IMAGE:$BUILD_NUMBER


                    '''

                }


            }

        }




        stage('Deploy to Kubernetes') {

            steps {

                sh '''

                kubectl apply -f kubernetes/

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
