#!/bin/bash

# Docker清理脚本
# 用于清理ApeRAG项目的Docker容器、镜像、卷等资源

set -o errexit
set -o pipefail
set -o nounset

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
Docker清理脚本 - ApeRAG项目

用法: $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -c, --containers        只清理容器（保留数据卷）
    -v, --volumes           清理容器和数据卷（⚠️ 会删除所有数据）
    -i, --images            清理未使用的镜像
    -a, --all               完全清理（容器、卷、镜像、网络）
    -s, --system            清理系统（容器、网络、镜像，不包括卷）
    -f, --force             强制执行，不询问确认
    --status                显示当前Docker资源状态
    --restart               清理后重新启动服务

示例:
    $0 -c                  # 只清理容器
    $0 -v                  # 清理容器和数据卷
    $0 -a                  # 完全清理
    $0 --status            # 查看资源状态
    $0 -c --restart        # 清理容器后重启

⚠️  警告: 使用 -v 或 -a 选项会删除所有数据，包括数据库！

EOF
}

# 显示当前状态
show_status() {
    print_info "当前Docker资源状态:"
    echo ""
    
    echo "=== 容器 ==="
    docker ps -a --filter "name=aperag" --format "table {{.Names}}\t{{.Status}}\t{{.Size}}" 2>/dev/null || echo "无法获取容器信息"
    echo ""
    
    echo "=== 卷 ==="
    docker volume ls --filter "name=aperag" 2>/dev/null || echo "无法获取卷信息"
    echo ""
    
    echo "=== 镜像 ==="
    docker images --filter "reference=*aperag*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null || echo "无法获取镜像信息"
    echo ""
    
    echo "=== 磁盘使用 ==="
    docker system df 2>/dev/null || echo "无法获取磁盘使用信息"
    echo ""
}

# 确认操作
confirm_action() {
    local message=$1
    if [ "${FORCE:-false}" = "true" ]; then
        return 0
    fi
    
    read -p "$(echo -e ${YELLOW}${message}${NC} [y/N]): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "操作已取消"
        exit 0
    fi
}

# 清理容器
cleanup_containers() {
    print_info "清理容器..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
        print_success "容器已停止并删除"
    else
        print_warning "未找到docker-compose.yml，尝试手动清理..."
        docker stop $(docker ps -aq --filter "name=aperag") 2>/dev/null || true
        docker rm $(docker ps -aq --filter "name=aperag") 2>/dev/null || true
        print_success "容器已清理"
    fi
}

# 清理容器和卷
cleanup_containers_and_volumes() {
    print_warning "⚠️  这将删除所有数据卷，包括数据库数据！"
    confirm_action "确定要继续吗？"
    
    print_info "清理容器和数据卷..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down -v
        print_success "容器和数据卷已删除"
    else
        print_warning "未找到docker-compose.yml，尝试手动清理..."
        docker stop $(docker ps -aq --filter "name=aperag") 2>/dev/null || true
        docker rm $(docker ps -aq --filter "name=aperag") 2>/dev/null || true
        docker volume rm $(docker volume ls -q --filter "name=aperag") 2>/dev/null || true
        print_success "容器和数据卷已清理"
    fi
}

# 清理镜像
cleanup_images() {
    print_info "清理未使用的镜像..."
    docker image prune -a -f
    print_success "未使用的镜像已清理"
}

# 清理系统
cleanup_system() {
    print_info "清理系统资源（容器、网络、镜像，不包括卷）..."
    docker system prune -a -f
    print_success "系统资源已清理"
}

# 完全清理
cleanup_all() {
    print_warning "⚠️  这将删除所有容器、卷、镜像和网络！"
    print_warning "⚠️  所有数据将被永久删除！"
    confirm_action "确定要继续吗？"
    
    print_info "执行完全清理..."
    
    # 清理容器和卷
    if [ -f "docker-compose.yml" ]; then
        docker-compose down -v
    else
        docker stop $(docker ps -aq) 2>/dev/null || true
        docker rm $(docker ps -aq) 2>/dev/null || true
        docker volume prune -f
    fi
    
    # 清理所有未使用的资源
    docker system prune -a --volumes -f
    
    print_success "完全清理完成"
}

# 重启服务
restart_services() {
    print_info "重新启动服务..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d
        print_success "服务已启动"
    else
        print_error "未找到docker-compose.yml，无法自动启动服务"
        print_info "请手动运行: docker-compose up -d"
    fi
}

# 主函数
main() {
    local cleanup_containers_only=false
    local cleanup_volumes=false
    local cleanup_images_only=false
    local cleanup_system_only=false
    local cleanup_all_resources=false
    local show_status_only=false
    local restart_after_cleanup=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--containers)
                cleanup_containers_only=true
                shift
                ;;
            -v|--volumes)
                cleanup_volumes=true
                shift
                ;;
            -i|--images)
                cleanup_images_only=true
                shift
                ;;
            -s|--system)
                cleanup_system_only=true
                shift
                ;;
            -a|--all)
                cleanup_all_resources=true
                shift
                ;;
            -f|--force)
                export FORCE=true
                shift
                ;;
            --status)
                show_status_only=true
                shift
                ;;
            --restart)
                restart_after_cleanup=true
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果没有参数，显示帮助
    if [ $# -eq 0 ] && [ "$cleanup_containers_only" = false ] && [ "$cleanup_volumes" = false ] && [ "$cleanup_images_only" = false ] && [ "$cleanup_system_only" = false ] && [ "$cleanup_all_resources" = false ] && [ "$show_status_only" = false ]; then
        show_help
        exit 0
    fi
    
    # 显示状态
    if [ "$show_status_only" = true ]; then
        show_status
        exit 0
    fi
    
    # 执行清理操作
    if [ "$cleanup_all_resources" = true ]; then
        cleanup_all
    elif [ "$cleanup_volumes" = true ]; then
        cleanup_containers_and_volumes
    elif [ "$cleanup_containers_only" = true ]; then
        cleanup_containers
    elif [ "$cleanup_images_only" = true ]; then
        cleanup_images
    elif [ "$cleanup_system_only" = true ]; then
        cleanup_system
    fi
    
    # 重启服务
    if [ "$restart_after_cleanup" = true ]; then
        restart_services
    fi
    
    # 显示最终状态
    echo ""
    print_info "清理完成！"
    show_status
}

# 运行主函数
main "$@"

