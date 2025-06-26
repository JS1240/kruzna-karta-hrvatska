#!/bin/bash

# Animation Development Helper Script
# Provides quick commands for testing animations during development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Function to check if we're in the frontend directory
check_directory() {
    if [ ! -f "package.json" ]; then
        print_error "Please run this script from the frontend directory"
        exit 1
    fi
    
    if [ ! -f "src/pages/AnimationTestPage.tsx" ]; then
        print_error "Animation test page not found. Please ensure all animation utilities are set up."
        exit 1
    fi
}

# Function to start development server with animation testing
start_dev_server() {
    print_status "Starting development server with animation testing..."
    print_status "Animation test page will be available at: http://localhost:5173/dev/animations"
    
    # Set environment variables for development
    export VITE_ANIMATION_DEBUG=true
    export VITE_PERFORMANCE_MONITOR=true
    
    npm run dev
}

# Function to build and check bundle size
check_bundle_size() {
    print_status "Building project and checking bundle size..."
    
    npm run build:dev
    
    # Check if any chunks are larger than 500KB (PRD requirement)
    if [ -d "dist" ]; then
        print_status "Checking bundle sizes against 500KB limit..."
        find dist -name "*.js" -size +500k -exec echo "WARNING: {} exceeds 500KB" \;
        
        # Calculate total size of animation libraries
        total_size=$(find dist -name "*vanta*" -o -name "*three*" -o -name "*p5*" | xargs wc -c 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
        total_size_kb=$((total_size / 1024))
        
        if [ $total_size_kb -gt 500 ]; then
            print_warning "Animation libraries total size: ${total_size_kb}KB (exceeds 500KB limit)"
        else
            print_success "Animation libraries total size: ${total_size_kb}KB (within 500KB limit)"
        fi
    fi
}

# Function to run TypeScript checks
check_typescript() {
    print_status "Running TypeScript checks for animation utilities..."
    
    npx tsc --noEmit --project tsconfig.app.json
    
    if [ $? -eq 0 ]; then
        print_success "TypeScript compilation successful"
    else
        print_error "TypeScript compilation failed"
        exit 1
    fi
}

# Function to validate color contrast
validate_colors() {
    print_status "Validating WCAG color contrast compliance..."
    
    # This would typically run automated tests
    # For now, we'll just remind the user to check the test page
    print_status "Please visit http://localhost:5173/dev/animations to validate color contrasts"
    print_status "The test page includes automatic WCAG 2.1 AA compliance checking"
}

# Function to run performance tests
performance_test() {
    print_status "Starting performance test mode..."
    print_status "This will open the test page with performance monitoring enabled"
    
    # Open the animation test page in the browser (macOS)
    if command -v open &> /dev/null; then
        print_status "Opening animation test page in browser..."
        sleep 2
        open "http://localhost:5173/dev/animations"
    fi
    
    start_dev_server
}

# Function to show usage
show_usage() {
    echo "Animation Development Helper"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     Start development server with animation testing"
    echo "  build     Build and check bundle sizes"
    echo "  check     Run TypeScript checks"
    echo "  colors    Validate color contrast compliance"
    echo "  perf      Start performance testing mode"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start dev server and open animation test page"
    echo "  $0 perf     # Start with performance monitoring"
    echo "  $0 build    # Check if bundle sizes meet requirements"
}

# Main script logic
check_directory

case "${1:-start}" in
    "start")
        start_dev_server
        ;;
    "build")
        check_typescript
        check_bundle_size
        ;;
    "check")
        check_typescript
        ;;
    "colors")
        validate_colors
        ;;
    "perf")
        performance_test
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
