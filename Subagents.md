# Subagents

This project leverages Claude Code's powerful subagent system for specialized tasks and domain expertise. **ALWAYS use subagents for complex, multi-step tasks, domain-specific work, and comprehensive analysis and do it in parallel.**

## Core Principle: Always Use Subagents

**Mandatory Subagent Usage**:
- **Complex Tasks**: Any task requiring 3+ steps or cross-domain knowledge
- **Specialized Domains**: Backend architecture, frontend optimization, security, performance
- **Production Issues**: System outages, debugging, incident response
- **Comprehensive Analysis**: Code reviews, architectural assessment, system-wide changes
- **Quality Assurance**: Testing, validation, compliance, security auditing

## Available Subagents

### 🏗️ Development & Implementation

**`general-purpose`**
- **Purpose**: Multi-step research and complex task execution with comprehensive analysis
- **When to use**: Open-ended research, complex problem-solving, multi-domain tasks
- **Capabilities**: File search, code analysis, documentation research, system understanding

**`backend-architect`** 
- **Purpose**: API design, server-side architecture, and scalable system design
- **When to use**: Designing new services, API endpoints, database schemas, system architecture
- **Capabilities**: FastAPI patterns, SQLAlchemy optimization, microservices design

**`frontend-component-builder`**
- **Purpose**: React components, responsive layouts, and frontend performance optimization
- **When to use**: Building UI components, implementing responsive design, client-side optimization
- **Capabilities**: React 19, TypeScript, Tailwind CSS, Mapbox integration, performance hooks

**`deployment-engineer`**
- **Purpose**: CI/CD pipelines, Docker containers, and cloud deployment automation
- **When to use**: Setting up deployments, containerization, infrastructure automation
- **Capabilities**: Docker, GitHub Actions, cloud platforms, production configurations

**`javascript-pro`**
- **Purpose**: Modern JavaScript development, async programming, and complex JS architectures
- **When to use**: Advanced JavaScript patterns, async/await optimization, Node.js performance
- **Capabilities**: ES2023+ features, async patterns, performance optimization, bundle analysis

**`python-expert`**
- **Purpose**: Advanced Python development, performance optimization, and complex algorithms
- **When to use**: Python optimization, advanced features, algorithm implementation, data processing
- **Capabilities**: Python 3.12+, async programming, performance profiling, memory optimization

### 🔍 Analysis & Quality

**`code-reviewer`**
- **Purpose**: Comprehensive code review for quality, security, and maintainability
- **When to use**: ALWAYS after significant code changes, before merging, for quality assessment
- **Capabilities**: Security analysis, best practices validation, performance review, documentation review

**`architect-reviewer`**
- **Purpose**: Architectural consistency, design patterns, and system integrity validation
- **When to use**: After structural changes, new services, API modifications, system refactoring
- **Capabilities**: SOLID principles validation, pattern consistency, architectural compliance

**`security-auditor`**
- **Purpose**: Security reviews, vulnerability assessment, and OWASP compliance
- **When to use**: Authentication systems, payment processing, data handling, security-critical code
- **Capabilities**: Threat modeling, vulnerability scanning, compliance validation, secure coding

**`performance-engineer`**
- **Purpose**: Application performance optimization, bottleneck identification, and scalability
- **When to use**: Performance issues, optimization needs, scalability planning, load testing
- **Capabilities**: Profiling, benchmarking, caching strategies, database optimization

**`error-debugger`**
- **Purpose**: Systematic error investigation and technical issue resolution
- **When to use**: Encountering errors, test failures, unexpected behavior, debugging sessions
- **Capabilities**: Root cause analysis, error pattern recognition, systematic debugging

**`error-detective`**
- **Purpose**: Production error analysis, log investigation, and distributed system debugging
- **When to use**: Production outages, error pattern analysis, log correlation, system failures
- **Capabilities**: Log analysis, error correlation, distributed tracing, anomaly detection

### 🌐 Infrastructure & Operations

**`devops-troubleshooter`** 
- **Purpose**: Production system issues, outages, and infrastructure problem resolution
- **When to use**: Production incidents, system degradation, infrastructure failures, emergency response
- **Capabilities**: System monitoring, log analysis, infrastructure debugging, incident response

**`cloud-architect`**
- **Purpose**: Cloud infrastructure design, cost optimization, and scalability planning
- **When to use**: Infrastructure planning, cost optimization, auto-scaling, serverless architecture
- **Capabilities**: AWS/Azure/GCP, Infrastructure as Code, cost analysis, scalability design

**`terraform-specialist`**
- **Purpose**: Infrastructure as Code with Terraform, state management, and module development
- **When to use**: Infrastructure automation, Terraform modules, state management, resource provisioning
- **Capabilities**: Terraform, resource management, state operations, provider configurations

**`database-optimizer`**
- **Purpose**: Database performance optimization, query tuning, and schema design
- **When to use**: Slow queries, database design, performance issues, schema optimization
- **Capabilities**: PostgreSQL optimization, query analysis, indexing strategies, schema design

**`database-admin`**
- **Purpose**: Database operations, maintenance, backup strategies, and reliability
- **When to use**: Database setup, backup configuration, maintenance tasks, operational issues
- **Capabilities**: Database administration, backup strategies, monitoring, disaster recovery

**`network-engineer`**
- **Purpose**: Network connectivity, load balancers, DNS, SSL/TLS, and traffic optimization
- **When to use**: Network issues, load balancing, SSL configuration, connectivity problems
- **Capabilities**: Network diagnostics, load balancer configuration, SSL/TLS setup, traffic analysis

### 🧠 Specialized Domains

**`ai-engineer`**
- **Purpose**: LLM applications, RAG systems, AI-powered features, and vector databases
- **When to use**: Building AI features, chatbots, content generation, AI integrations
- **Capabilities**: OpenAI API, RAG implementation, prompt engineering, vector databases

**`ml-production-engineer`**
- **Purpose**: ML model deployment, inference optimization, and production ML systems
- **When to use**: Deploying ML models, model serving, A/B testing, model monitoring
- **Capabilities**: Model deployment, TorchServe, inference optimization, model monitoring

**`mlops-engineer`**
- **Purpose**: ML pipelines, experiment tracking, model registries, and ML infrastructure
- **When to use**: ML pipeline setup, experiment tracking, model versioning, ML infrastructure
- **Capabilities**: MLflow, model registries, pipeline orchestration, ML automation

**`data-engineer`**
- **Purpose**: Data pipelines, ETL processes, data warehouses, and analytics infrastructure
- **When to use**: Data processing, ETL pipelines, analytics setup, data architecture
- **Capabilities**: Apache Spark, data pipelines, ETL design, data warehouse architecture

**`ui-ux-designer`**
- **Purpose**: Interface design, wireframes, user flows, and accessibility optimization
- **When to use**: Designing interfaces, user experience optimization, accessibility improvements
- **Capabilities**: Wireframing, user flows, design systems, accessibility standards

**`ios-developer`**
- **Purpose**: Native iOS development, SwiftUI/UIKit, and App Store optimization
- **When to use**: iOS app development, Swift programming, mobile-specific features
- **Capabilities**: SwiftUI, UIKit, Core Data, iOS patterns, App Store guidelines

### 📋 Business & Documentation

**`prd-specialist`** *(Recently Added)*
- **Purpose**: Product Requirements Documents, business strategy, and technical architecture alignment
- **When to use**: Creating PRDs, product planning, feature specifications, strategic documentation
- **Capabilities**: Business analysis, technical requirements, user research integration, roadmap planning

**`business-analyst`**
- **Purpose**: Metrics analysis, KPI tracking, revenue projections, and business intelligence
- **When to use**: Business metrics analysis, performance tracking, revenue analysis, reporting
- **Capabilities**: Data analysis, KPI definition, business intelligence, financial modeling

**`content-marketer`**
- **Purpose**: Marketing content creation, SEO optimization, and content strategy
- **When to use**: Creating marketing materials, blog posts, SEO content, social media campaigns
- **Capabilities**: Content creation, SEO optimization, social media strategy, brand messaging

**`legal-advisor`**
- **Purpose**: Legal documentation, privacy policies, terms of service, and compliance
- **When to use**: Legal documentation, GDPR compliance, terms creation, regulatory requirements
- **Capabilities**: Legal document drafting, privacy policy creation, compliance validation

**`customer-support-specialist`**
- **Purpose**: Customer inquiries, support documentation, and user experience optimization
- **When to use**: Customer support processes, FAQ creation, user documentation, support optimization
- **Capabilities**: Support workflow design, documentation creation, customer communication

### 🧪 Quality & Testing

**`test-automator`**
- **Purpose**: Comprehensive test suites, test automation, and coverage improvement
- **When to use**: Setting up testing, improving coverage, test automation, quality assurance
- **Capabilities**: Unit tests, integration tests, E2E tests, test automation frameworks

**`test-runner`**
- **Purpose**: Test execution, failure analysis, and test result interpretation
- **When to use**: Running tests, analyzing failures, test debugging, test optimization
- **Capabilities**: Test execution, failure analysis, test debugging, performance testing

**`dx-optimizer`**
- **Purpose**: Developer experience optimization, workflow improvement, and tooling enhancement
- **When to use**: Improving development workflows, tooling setup, developer productivity
- **Capabilities**: Workflow optimization, tooling configuration, developer experience design

### 🔧 Specialized Technologies

**`payment-integration-specialist`**
- **Purpose**: Payment processing, billing systems, and financial transaction handling
- **When to use**: Payment integration, subscription billing, financial features, PCI compliance
- **Capabilities**: Stripe/PayPal integration, subscription systems, payment security, compliance

**`rust-systems-engineer`**
- **Purpose**: Rust development, systems programming, and performance-critical applications
- **When to use**: Rust development, systems programming, performance optimization, memory safety
- **Capabilities**: Rust programming, systems design, memory management, concurrent programming

**`legacy-modernizer`**
- **Purpose**: Legacy system modernization, framework migration, and technical debt reduction
- **When to use**: Modernizing old code, framework upgrades, technical debt reduction
- **Capabilities**: Migration planning, framework modernization, refactoring strategies

**`prompt-engineer`**
- **Purpose**: LLM prompt optimization, AI system performance, and prompt effectiveness
- **When to use**: Optimizing AI prompts, improving AI performance, prompt design
- **Capabilities**: Prompt optimization, AI system tuning, prompt effectiveness analysis

### 📊 Financial & Analytics

**`risk-manager`**
- **Purpose**: Portfolio risk assessment, position sizing, and risk management strategies
- **When to use**: Financial risk analysis, investment decisions, risk assessment
- **Capabilities**: Risk analysis, portfolio management, financial modeling

**`quant-analyst`**
- **Purpose**: Quantitative finance, algorithmic trading, and financial modeling
- **When to use**: Financial analysis, trading strategies, quantitative modeling
- **Capabilities**: Financial modeling, algorithmic trading, statistical analysis

### 🔍 Research & Investigation

**`search-specialist`**
- **Purpose**: Comprehensive web research, competitive analysis, and information gathering
- **When to use**: Market research, competitive analysis, information gathering, fact-checking
- **Capabilities**: Web research, data gathering, analysis synthesis, trend identification

**`incident-responder`**
- **Purpose**: Critical production incidents, emergency response, and crisis management
- **When to use**: Production outages, critical system failures, emergency situations
- **Capabilities**: Incident coordination, emergency response, crisis communication, post-mortem analysis

## Subagent Selection Guidelines

### Task Complexity Assessment
- **Simple** (1-2 steps): Consider direct implementation
- **Moderate** (3-5 steps): **ALWAYS use appropriate subagent**
- **Complex** (6+ steps): **ALWAYS use multiple subagents or general-purpose**

### Domain Matching
1. **Identify primary domain**: Backend, frontend, infrastructure, analysis, etc.
2. **Select specialized subagent**: Match task to subagent expertise
3. **Consider secondary domains**: Use multiple subagents for cross-domain tasks
4. **Quality assurance**: Always use reviewer subagents for significant changes

### Croatian Events Platform Specific Usage

**Common Scenarios**:
- **New scraper development**: `backend-architect` → `python-expert` → `code-reviewer`
- **Map feature enhancement**: `frontend-component-builder` → `performance-engineer` → `test-automator`
- **Database optimization**: `database-optimizer` → `performance-engineer` → `architect-reviewer`
- **Production issues**: `devops-troubleshooter` → `error-detective` → `incident-responder`
- **Security features**: `security-auditor` → `backend-architect` → `code-reviewer`
- **API development**: `backend-architect` → `python-expert` → `test-automator` → `code-reviewer`

## Best Practices

### Before Starting Any Task
1. **Assess complexity**: Is this a multi-step or specialized task?
2. **Identify domains**: What expertise areas are involved?
3. **Select subagents**: Choose the most appropriate specialized agents
4. **Plan sequence**: Determine if subagents should work in parallel or sequence

### During Development
1. **Use multiple subagents**: Don't rely on a single agent for complex tasks
2. **Leverage specialization**: Each subagent brings unique expertise and patterns
3. **Quality gates**: Always use reviewer subagents for significant changes
4. **Documentation**: Let subagents handle their specialty areas

### Quality Assurance
1. **Code review**: `code-reviewer` for all significant code changes
2. **Architecture review**: `architect-reviewer` for structural changes
3. **Security review**: `security-auditor` for security-sensitive code
4. **Performance review**: `performance-engineer` for optimization needs

## Integration with Development Workflow

**Standard Task Flow**:
1. **Analysis**: Use `general-purpose` or domain-specific analyst
2. **Implementation**: Use appropriate implementation subagents
3. **Testing**: Use `test-automator` and `test-runner`
4. **Review**: Use appropriate reviewer subagents
5. **Deployment**: Use `deployment-engineer` or `devops-troubleshooter`

**Emergency Response Flow**:
1. **Initial response**: `incident-responder` for coordination
2. **Investigation**: `error-detective` for root cause analysis
3. **Resolution**: Domain-specific subagents for fixes
4. **Validation**: `test-runner` and reviewers for verification

This comprehensive subagent system ensures that every task is handled by specialized expertise, resulting in higher quality, more efficient development, and better outcomes for the Croatian Events Platform.