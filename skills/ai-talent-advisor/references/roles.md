# AI Roles in an Agentic SDLC Delivery Organization

## Table of Contents
1. [Role Summary Table](#role-summary-table)
2. [Forward Deployed Architect (FDA)](#fda)
3. [Forward Deployed Engineer (FDE)](#fde)
4. [Applied AI Specialist](#applied-ai-specialist)
5. [AI Engineer](#ai-engineer)
6. [Project Staffing Model](#project-staffing-model)
7. [Resource Sourcing](#resource-sourcing)
8. [Role Relationships](#role-relationships)
9. [Common Myths & Misconceptions](#myths)

---

## Role Summary Table

| Role | Typical Background | Primary Responsibility | Key Deliverables | Typical Source |
|------|---------------------|------------------------|------------------|----------------|
| **Forward Deployed Architect (FDA)** | Enterprise/Solution/Application Architect | Design the Agentic SDLC architecture for a specific IT domain and client | End-to-end Agentic SDLC architecture, agent decomposition, governance, evaluation framework | Domain service line |
| **Forward Deployed Engineer (FDE)** | Solution Architect, Senior Technical Lead, Application Architect | Implement the Agentic SDLC designed by the FDA | Agent skills, reusable workflows, project context, specifications, automation | Domain service line |
| **Applied AI Specialist** | Developer, Senior Developer, Technical Specialist | Use AI-enabled development practices during day-to-day delivery | Software delivered using AI-first practices, improved specifications, enhanced agents | Domain delivery practice |
| **AI Engineer** | AI/ML Engineer, Python Engineer | Build complex AI capabilities that cannot be assembled using existing agent tooling | Custom agents, orchestration services, reusable AI infrastructure | Advanced Analytics & AI Practice |

---

## Forward Deployed Architect (FDA) {#fda}

### Background
Experienced Enterprise Architect, Application Architect, or Solution Architect. Must become hands-on with modern AI-enabled software engineering.

### Core Responsibility
Designs the **Agentic SDLC** for a specific IT domain and client. The Agentic SDLC varies significantly by domain:
- Digital Engineering
- Data Engineering
- Data Platforms
- Testing & Quality Engineering
- Integration
- Mainframe Modernization

Each domain has different SDLC activities, artifacts, reviews, and automation opportunities.

### AI Responsibilities
Designs:
- Overall Agentic SDLC architecture
- Agent architecture and agent decomposition
- Workflow orchestration and agent interactions
- Human approval points and autonomy boundaries
- Evaluation strategy, safety and security controls
- Agent governance and continuous improvement framework

Also introduces: Context Engineering, Prompt Engineering, Evaluation & Validation (Evals)

### Ongoing Responsibilities
Continuously measures: delivery velocity, software quality, automation coverage, engineering productivity, autonomy levels.

### Band: 9–10

---

## Forward Deployed Engineer (FDE) {#fde}

### Background
Application Architect, Solution Designer, or Senior Technical Lead with strong SDLC knowledge and hands-on AI engineering skills.

### Core Responsibility
Implements the Agentic SDLC designed by the FDA.

### Key Activities
Creates:
- Agent skills centred around `SKILL.md`
- Reusable skill packages and agent workflows
- Multi-agent interactions and SDLC automation

### Spec-Driven Development
FDE is a principal practitioner of **Spec-Driven Development (SDD)**:
- Specification-first engineering
- Structured requirements and design specifications
- Implementation specifications
- Automated execution from specifications

### Context Engineering
Assembles complete project context:
- Requirements, architecture, standards, coding guidelines
- Design documents, previous artifacts, reviews
- Meeting recordings, project knowledge, structured metadata

### Band: 8–9

---

## Applied AI Specialist {#applied-ai-specialist}

### Background
Developers and Senior Developers who are domain delivery experts.

### Core Responsibility
Use AI to accelerate day-to-day software delivery.

### Required Tools
- GitHub Copilot, Cursor, AWS Kiro, IBM Bob
- Other enterprise coding agents and Agentic IDEs

### Expected Competencies
- Prompt engineering, specification writing
- Context windows, tool calls, permissions
- Model behaviour, limitations, review practices, verification

### As They Mature
- Create simple agents and improve existing agents
- Refine prompts and improve specifications

### Band: 6–8

---

## AI Engineer {#ai-engineer}

### Background
AI engineering specialist with strong software engineering capabilities. Sourced from **Advanced Analytics & AI Practice** (not from domain service lines).

### Core Responsibility
Develop advanced AI capabilities beyond standard enterprise agent tooling.

### Required Skills
- Python, LangGraph, LangChain
- Retrieval-Augmented Generation (RAG)
- MCP integrations, Agent orchestration, Tool development

### Typical Responsibilities
Build:
- Custom agent frameworks and orchestration services
- Python-based agents and reusable AI services
- Advanced integrations and complex multi-agent workflows

### Important Note
The AI Engineer is a **specialist role** — not a substitute for FDE or Applied AI Specialist. Only needed when enterprise tooling is genuinely insufficient for the required capability.

---

## Project Staffing Model {#project-staffing-model}

First step: identify the **IT domain** (Digital Engineering, Data Engineering, Data Platforms, Testing, Integration, etc.).

Domain architects and engineers are then trained in:
- Agentic SDLC, Prompt Engineering, Context Engineering
- Spec-Driven Development, Agent Skills (`SKILL.md`)
- Agent workflows, Modern coding agents and Agentic IDEs

| Band | Role |
|------|------|
| Band 9–10 | Forward Deployed Architect (FDA) |
| Band 8–9 | Forward Deployed Engineer (FDE) |
| Band 6–8 | Applied AI Specialist |

The AI Engineer remains a specialist role used where custom AI capabilities or complex orchestration are required — **not a default team member**.

---

## Resource Sourcing {#resource-sourcing}

| Role | Source Organization |
|------|---------------------|
| Forward Deployed Architect | Domain Consulting Service Line |
| Forward Deployed Engineer | Domain Consulting Service Line |
| Applied AI Specialist | Domain Consulting Service Line |
| AI Engineer | Advanced Analytics & AI Practice |

---

## Role Relationships {#role-relationships}

```
          Forward Deployed Architect (FDA)
                        │
          Designs the Agentic SDLC Architecture
                        │
         ┌──────────────┴──────────────┐
         │                             │
Forward Deployed Engineer        AI Engineer
Implements the architecture    Builds custom AI capabilities
         │                             │
         └──────────────┬──────────────┘
                        │
           Applied AI Specialists
 Use coding agents to deliver software within
       the Agentic SDLC on day-to-day work
```

- **FDA** defines what the Agentic SDLC should look like
- **FDE** implements how it operates within the delivery process
- **Applied AI Specialists** execute software delivery using AI-first engineering practices
- **AI Engineers** extend the platform only where enterprise tooling is insufficient

---

## Common Myths & Misconceptions {#myths}

| Myth | Reality |
|------|---------|
| "AI Engineer = anyone who uses AI" | AI Engineer is a specific specialist (Python/LangGraph/RAG) from Advanced Analytics & AI. Most projects don't need one. |
| "FDA and FDE are the same role" | FDA *designs* the architecture; FDE *implements* it. Different seniority, different deliverables. |
| "Applied AI Specialists replace developers" | They ARE developers — senior devs who use AI tooling to accelerate delivery. Domain expertise is still essential. |
| "We need an AI Engineer to build agents" | FDEs build most agent capabilities using SKILL.md and existing tooling. AI Engineers only needed for complex custom orchestration. |
| "One FDA covers all domains" | FDA expertise is domain-specific. A Digital Engineering FDA has different knowledge than a Data Engineering FDA. |
| "FDE is just a senior developer" | FDE implements Agentic SDLC — they need architecture-level thinking, context engineering, and hands-on AI skills beyond typical dev work. |
| "Applied AI Specialists don't need AI architecture knowledge" | They need to understand model behaviour, context windows, tool calls, and review practices to use AI effectively and safely. |
| "AI Engineer is needed on every project" | AI Engineer is only needed when enterprise agent tooling is genuinely insufficient. Most projects are served by FDA + FDE + Applied AI Specialists. |
