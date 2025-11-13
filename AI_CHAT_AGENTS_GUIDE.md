# AI Chat Agents - Available Pages

## 🤖 Two Conversational AI Agents Available!

When you run the application, you have **TWO pages** with extended conversational AI chat:

### Page 4: 📊 Project Database with AI Chat
**Purpose:** Query and filter the project database using natural language

**Conversational Features:**
- ✅ Multi-turn conversations with context memory
- ✅ Follow-up questions supported
- ✅ AI remembers previous queries in the conversation
- ✅ Natural language project filtering

**Example Conversations:**
```
You: "Show me all projects in financial services"
AI: [Filters and shows results]

You: "Now filter only projects from 2024-2025"
AI: [Applies additional filter, remembers previous context]

You: "Who was the partner on these projects?"
AI: [Provides partner information from filtered results]
```

**Features:**
- Natural language query interpretation
- Smart filtering across multiple columns
- Follow-up question handling
- Statistics and visualizations
- Export to CSV/Excel
- Password protected (bud123)

---

### Page 6: 🤖 PowerPoint Generator (Credentials Chat Agent)
**Purpose:** Generate PowerPoint presentations with credentials using conversational AI

**Conversational Features:**
- ✅ Multi-step interactive dialogue
- ✅ AI asks clarifying questions
- ✅ Remembers choices throughout the conversation
- ✅ Natural language filter requests
- ✅ Context-aware responses

**Example Conversation:**
```
You: "Fill template with Bud van der Schier"
AI: "Found 15 projects! Would you like to filter? (e.g., 'Only 2024-2025' or 'skip')"

You: "Only financial services from 2024-2025"
AI: "Filtered to 8 projects. How many would you like in the presentation?"

You: "5"
AI: "Include detailed descriptions? (yes/no)"

You: "yes"
AI: [Generates PowerPoint with AI-enhanced descriptions]
```

**Features:**
- Natural language credential requests
- AI-powered project filtering
- Intelligent project selection (most recent + diverse)
- Dynamic description generation
- Interactive multi-turn conversation
- PowerPoint template filling
- Download generated presentations

---

## 🚀 How to Access

**Option 1: Launch the main app**
```bash
cd room_allocator_strategy_2
streamlit run app.py
```

**Option 2: Use the launch script (if available)**
```bash
./Launch_Project_Database.bat
```

Then navigate using the sidebar:
- Select **Page 4** for Project Database AI Chat
- Select **Page 6** for PowerPoint Generator AI Chat

---

## 🔐 Requirements

**Both AI Agents require:**
- ✅ KPMG network access (VPN or on-premises)
- ✅ KPMG Workbench API access (pre-configured)
- ✅ Internet connection

**For Project Database (Page 4):**
- Password: `bud123`
- Database: `credentials_full.xlsx`

**For PowerPoint Generator (Page 6):**
- Database: `credentials_full.xlsx`
- Template: `Bud van der Schier– Partner.pptx`

---

## 💡 Key Differences

| Feature | Project Database (Page 4) | PowerPoint Generator (Page 6) |
|---------|---------------------------|-------------------------------|
| **Purpose** | Query/filter projects | Generate PowerPoint presentations |
| **Input** | Natural language queries | Conversational requests |
| **Output** | Filtered data + statistics | PowerPoint file (.pptx) |
| **Conversation Type** | Open-ended Q&A | Guided multi-step workflow |
| **AI Features** | Query interpretation, filtering | Filtering, selection, description generation |
| **Export** | CSV/Excel | PowerPoint |
| **Password** | Required (bud123) | Not required |

---

## 🎯 Use Cases

**Use Project Database (Page 4) when you want to:**
- Explore the project database
- Find projects by industry, partner, manager, year
- Get statistics and insights
- Export filtered results
- Ask questions about the data
- Browse projects interactively

**Use PowerPoint Generator (Page 6) when you want to:**
- Create credential presentations
- Generate PowerPoint slides automatically
- Fill templates with selected projects
- Get AI-enhanced project descriptions
- Produce professional presentations quickly
- Select specific partner/manager credentials

---

## 🌟 Both Agents Are Production-Ready!

✅ **Conversational AI** - Both maintain conversation context  
✅ **User-Friendly** - Natural language interfaces  
✅ **Integrated** - Single application, multiple tools  
✅ **Downloadable** - Share via .bat file or Git  
✅ **Professional** - KPMG Workbench API integration  

---

**Ready to use!** Just launch the app and select the page you need from the sidebar. 🎉
