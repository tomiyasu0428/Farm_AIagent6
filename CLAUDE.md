# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Agri_AI6 project - an agricultural AI agent system designed to provide intelligent support to farm workers through LINE messaging. The system uses LangGraph for multi-agent architecture and MongoDB Atlas for hybrid search capabilities.

**Current Status**: This repository contains comprehensive design documentation but no implementation code yet. This is a greenfield project ready for development based on the detailed specifications in the `docs/` folder.

## Architecture

### Core Components

The system follows a **Supervisor-Worker multi-agent pattern** using LangGraph:

1. **SupervisorAgent**: Central orchestrator that receives LINE webhook messages, analyzes user intent, and delegates tasks to specialized agents
2. **ReadAgent**: Handles information retrieval using MongoDB Atlas hybrid search (combining keyword and vector search)
3. **WriteAgent**: Manages data writing operations including work record registration and confirmation workflows

### Technology Stack

- **AI/Agents**: Python 3.9+, LangChain, LangGraph
- **LLM**: Google Gemini Pro/Flash with text embedding models
- **Database**: MongoDB Atlas
  - Atlas Search: Keyword search with BM25 algorithm
  - Atlas Vector Search: Semantic search using embeddings
  - Hybrid search using `$rankFusion` stage for optimal results
- **Interface**: LINE Messaging API with LIFF (LINE Front-end Framework)
- **Infrastructure**: Google Cloud Functions (webhooks), Google Cloud Run (agent execution), Google Cloud Pub/Sub (async notifications)
- **Monitoring**: LangSmith

### Database Design

MongoDB collections use flexible schemas to support agricultural data:

- **farms**: Basic farm information
- **users**: LINE account integration with worker data
- **fields**: Field details with extensible `custom_properties` for farm-specific data
- **work_records**: Daily work records with dynamic `details` based on work type

Key design principle: **"Fixed core information + freely extensible custom information per farm"**

## Development Phases

The project is planned in 4 phases:

1. **Phase 1 (3 weeks)**: Basic foundation with Supervisor + ReadAgent implementing hybrid search for LINE Q&A
2. **Phase 2 (3 weeks)**: WriteAgent for work record registration via LINE + basic LIFF dashboard
3. **Phase 3 (4 weeks)**: RecommendationAgent for work suggestions + advanced LIFF features
4. **Phase 4 (4 weeks)**: NotificationAgent for proactive notifications + async processing infrastructure

## Key Technical Concepts

### Hybrid Search Strategy
- **Keyword search**: Effective for specific product names, model numbers, proper nouns
- **Vector search**: Effective for ambiguous expressions, contextual understanding
- **Combined approach**: Uses MongoDB's `$rankFusion` with Reciprocal Rank Fusion (RRF) algorithm

### State Management
Uses `AgriAgentState` with LangGraph for conversation context:
```python
class AgriAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    thread_id: str
    next_agent: str
    pending_confirmation: Dict[str, Any]
```

### LINE Integration
- **Chat Interface**: Natural language work reporting and simple Q&A
- **LIFF Interface**: Rich UI dashboards, work planning visualization, complex data input forms

## Key Documentation

The most important design documents are:
- `docs/LangGraph_マルチエージェント_要件定義書_v4.md`: Main requirements specification (v4.1)
- `docs/企画書：LangGraphとMongoDBハイブリッド検索を活用した次世代LINE AIエージェントの構築.md`: Technical architecture deep dive
- `docs/2025-07-26_農場管理AIエージェント完全開発ガイドのコピー.md`: Development guide with MongoDB flexibility focus

## Development Guidelines

### When implementing the system:

1. **Start with Phase 1**: Implement basic LINE webhook → LangGraph → MongoDB Atlas flow
2. **Use MongoDB Atlas features**: Leverage native hybrid search rather than separate vector databases
3. **Design for flexibility**: Use MongoDB's document model to allow farms to extend schemas dynamically
4. **Implement async processing**: LINE webhook responses must be immediate; use background tasks for heavy AI processing
5. **State persistence**: Use MongoDB as LangGraph checkpointer for conversation continuity
6. **Migrate existing assets**: The system builds upon "Agri_AI3" - reuse existing 11 LangChain tools and MongoDB schemas where possible

### Architecture Decisions

- **Single database approach**: MongoDB Atlas handles all data types (documents, vectors, search indexes, conversation state) to eliminate data synchronization complexity
- **Graph-based agent control**: LangGraph provides explicit control flow for complex agent interactions vs. linear chains
- **LINE-first interface**: Natural language primary interface with LIFF for complex visualizations
- **Hybrid search optimization**: Combine precise keyword matching with semantic understanding for agricultural domain queries

## Business Context

This system targets agricultural workers who need:
- Instant access to "what to do next" decisions while in the field
- Reduction of thinking/decision time from 10 minutes to 0 minutes
- Natural language work recording through LINE
- AI memory of past work and contextual recommendations

The goal is to create an AI partner that grows smarter with use and eliminates the cognitive load of agricultural decision-making.