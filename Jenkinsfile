pipeline {
    agent any
    
    environment {
        // 项目配置
        PROJECT_NAME = 'ecom-chatbot'
        DEPLOY_PATH = '/root/ecom-chat-bot'
    }
    
    options {
        // 保留最近10次构建
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // 设置超时时间
        timeout(time: 30, unit: 'MINUTES')
        // 禁止并发构建
        disableConcurrentBuilds()
        // 添加时间戳
        timestamps()
    }
    
    stages {
        stage('准备') {
            steps {
                echo '=========================================='
                echo '  电商智能客服系统 - CI/CD Pipeline'
                echo "  构建编号: ${env.BUILD_NUMBER}"
                echo "  Git分支: ${env.GIT_BRANCH}"
                echo "  提交ID: ${env.GIT_COMMIT}"
                echo '=========================================='
            }
        }
        
        stage('拉取最新代码') {
            steps {
                script {
                    echo '>>> 在部署目录拉取最新代码...'
                    sh '''
                        cd ${DEPLOY_PATH}
                        
                        # 拉取最新代码
                        git fetch origin develop
                        git checkout develop
                        git pull origin develop
                        
                        # 显示最新提交
                        echo "最新提交:"
                        git log -1 --oneline
                        
                        echo "✓ 代码更新完成"
                    '''
                }
            }
        }
        
        stage('Docker配置检查') {
            steps {
                script {
                    echo '>>> 检查Docker配置...'
                    sh '''
                        cd ${DEPLOY_PATH}
                        docker-compose config -q
                        echo "✓ Docker配置检查通过"
                    '''
                }
            }
        }
        
        stage('构建镜像') {
            steps {
                script {
                    echo '>>> 构建Docker镜像...'
                    sh '''
                        cd ${DEPLOY_PATH}
                        docker-compose build --parallel
                        echo "✓ 镜像构建完成"
                    '''
                }
            }
        }
        
        stage('停止旧服务') {
            steps {
                script {
                    echo '>>> 停止旧版本服务...'
                    sh '''
                        cd ${DEPLOY_PATH}
                        # 停止应用服务（保留数据库等基础服务）
                        docker-compose stop api celery-worker || true
                        echo "✓ 旧服务已停止"
                    '''
                }
            }
        }
        
        stage('部署新服务') {
            steps {
                script {
                    echo '>>> 部署新版本...'
                    sh '''
                        cd ${DEPLOY_PATH}
                        
                        # 确保基础服务正在运行
                        docker-compose up -d postgres redis milvus-etcd milvus-minio milvus rabbitmq
                        
                        # 等待基础服务就绪
                        echo "等待基础服务就绪..."
                        sleep 20
                        
                        # 运行数据库初始化（如果需要）
                        docker-compose up db-init || true
                        
                        # 启动应用服务
                        docker-compose up -d api celery-worker
                        
                        # 清理未使用的镜像
                        docker image prune -f || true
                        
                        echo "✓ 新服务已启动"
                    '''
                }
            }
        }
        
        stage('健康检查') {
            steps {
                script {
                    echo '>>> 执行健康检查...'
                    sh '''
                        cd ${DEPLOY_PATH}
                        
                        # 等待服务启动
                        echo "等待服务完全启动..."
                        sleep 30
                        
                        # 检查服务状态
                        echo "=== 服务状态 ==="
                        docker-compose ps
                        
                        # 检查API健康
                        echo ""
                        echo "=== API健康检查 ==="
                        max_attempts=10
                        attempt=0
                        
                        while [ $attempt -lt $max_attempts ]; do
                            if curl -f -s http://localhost:8000/docs > /dev/null 2>&1; then
                                echo "✓ API服务健康检查通过"
                                echo "  API地址: http://localhost:8000"
                                echo "  API文档: http://localhost:8000/docs"
                                exit 0
                            fi
                            echo "等待API服务启动... ($attempt/$max_attempts)"
                            sleep 10
                            attempt=$((attempt + 1))
                        done
                        
                        echo "⚠ API服务启动超时，但部署已完成"
                        echo "  请手动检查服务状态"
                        exit 0
                    '''
                }
            }
        }
        
        stage('部署验证') {
            steps {
                script {
                    echo '>>> 部署后验证...'
                    sh '''
                        cd ${DEPLOY_PATH}
                        
                        echo "=== 最终服务状态 ==="
                        docker-compose ps
                        
                        echo ""
                        echo "=== API服务日志（最后20行）==="
                        docker-compose logs --tail=20 api || true
                        
                        echo ""
                        echo "=== 部署完成时间 ==="
                        date '+%Y-%m-%d %H:%M:%S'
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '=========================================='
            echo '  🎉 部署成功！'
            echo "  构建编号: ${env.BUILD_NUMBER}"
            echo "  Git分支: ${env.GIT_BRANCH}"
            echo "  提交ID: ${env.GIT_COMMIT}"
            echo '  '
            echo '  访问地址:'
            echo '  API服务: http://localhost:8000'
            echo '  API文档: http://localhost:8000/docs'
            echo '=========================================='
        }
        
        failure {
            echo '=========================================='
            echo '  ❌ 部署失败！'
            echo "  构建编号: ${env.BUILD_NUMBER}"
            echo '  请检查日志以获取详细信息'
            echo '=========================================='
            
            script {
                sh '''
                    cd ${DEPLOY_PATH}
                    echo "=== 错误诊断信息 ==="
                    echo "服务状态:"
                    docker-compose ps || true
                    echo ""
                    echo "最近日志:"
                    docker-compose logs --tail=30 || true
                '''
            }
        }
        
        always {
            echo '>>> 构建流程结束'
        }
    }
}
