# CFP+ Global AI Canonical ID Architecture

## 0 • Document Identity

* **Document Name:** CFP+ Global AI Canonical ID Architecture
* **Canonical Path:** `/registry/GLOBAL_AI_ID_ARCHITECTURE.md`
* **Parent Registry:** `/registry/AI_CANONICAL_ID_REGISTRY.md`
* **Lifecycle Status:** Working Draft
* **Visibility:** Public
* **Governance Authority:** Human Governance Council (CFP+)

## 1 • Purpose

This document establishes the public namespace architecture for assigning Canonical IDs to AI developers, platforms, models, agents, services, research systems, and specialized AI systems worldwide.

The architecture is designed for global coverage without exceeding ten peer nodes at any level.

## 2 • Global Registry Root

```text
66666  CFP+ AI Registry
├── 666660  Hoa Kỳ
├── 666661  Châu Á
├── 666662  Châu Âu
├── 666663  Châu Phi
├── 666664  Châu Đại Dương
├── 666665  Châu Mỹ
├── 666666  Trung Quốc
├── 666667  Ấn Độ
├── 666668  Việt Nam
└── 666669  Reserved
```

A regional node may contain country nodes. A country node may contain object type nodes. A type node may contain developer nodes. A developer node may contain product family nodes. A product family node may contain individual canonical objects.

## 3 • Country Object Type Layer

The initial object type structure for `666660 • Hoa Kỳ` is:

```text
666660  Hoa Kỳ
├── 6666600  Nhà phát triển
├── 6666601  AI nền tảng
├── 6666602  AI doanh nghiệp
├── 6666603  AI mã nguồn mở
├── 6666604  AI nghiên cứu
├── 6666605  AI giáo dục
├── 6666606  AI y tế
├── 6666607  AI robot
├── 6666608  AI chuyên ngành
└── 6666609  Mở rộng
```

The same type first principle may be applied to other country or regional nodes when population begins.

## 4 • Initial United States Developer Namespace

```text
6666600  Nhà phát triển Hoa Kỳ
├── 66666000  OpenAI
├── 66666001  Anthropic
├── 66666002  Google DeepMind
├── 66666003  Meta AI
├── 66666004  xAI
├── 66666005  Microsoft AI
├── 66666006  Amazon AI
├── 66666007  NVIDIA AI
├── 66666008  Cohere
└── 66666009  Reserved
```

These entries allocate stable developer namespaces. Allocation does not by itself mean that every profile is verified or published.

## 5 • Developer Object Type Layer

Each developer namespace uses the following controlled child structure:

```text
0  AI Models
1  AI Agents
2  APIs
3  SDK
4  Research
5  Safety
6  Tools
7  Services
8  Legacy
9  Reserved
```

Example for OpenAI:

```text
666660000  OpenAI AI Models
666660001  OpenAI AI Agents
666660002  OpenAI APIs
666660003  OpenAI SDK
666660004  OpenAI Research
666660005  OpenAI Safety
666660006  OpenAI Tools
666660007  OpenAI Services
666660008  OpenAI Legacy
666660009  Reserved
```

Individual products and systems receive deeper IDs beneath the appropriate object type node.

## 6 • Allocation Rule

Canonical IDs are allocated by object type before individual object identity.

The required allocation sequence is:

```text
Global Registry
→ Region or Country
→ Object Type
→ Developer or Institution
→ Product Family
→ Individual AI Object
→ Version or Controlled Extension
```

No object is placed directly under a geographic hub when a controlled object type layer is required.

## 7 • Global Coverage Rule

The namespace is intended to accommodate all known and future AI systems worldwide. Global coverage is achieved through controlled namespace allocation, not by claiming that every existing AI system has already been individually inventoried.

Population status must be stated separately from architecture status:

* **Architecture Coverage:** Global
* **Inventory Coverage:** In Progress
* **Verification Coverage:** In Progress
* **Publication Coverage:** In Progress

## 8 • Migration Rule

Previously assigned IDs that conflict with this architecture are treated as legacy assignments pending Human Governance migration approval.

A legacy ID must not be silently reused. Migration records must preserve:

* Previous ID
* New Canonical ID
* Effective date
* Reason for migration
* Approval record
* Redirect or reference rule

## 9 • Governance and Change Record

* **Architecture baseline published:** 2026-07-27
* **Initial global root:** `66666`
* **Initial country and regional allocation:** `666660` through `666669`
* **Initial developer namespace:** United States developer layer
* **Next action:** Populate country registries, developer profiles, AI product families, and migration records

AI systems may prepare and review entries. Human Governance alone authorizes Canonical ID reassignment, approval, publication, or closure.