# Credentials Manager - Integration Guide

## ✅ What's Been Added

Two new pages have been added to the room_allocator_strategy_2 project:

### Page 5: Credential Browser 📋
**File:** `pages/5_Credential_Browser.py`

**Features:**
- Search credentials by person (partner/manager)
- Browse all projects with filters
- Multi-select filters (year, industry, sector)
- Search by client name
- Export to CSV/Excel
- No AI required - fast browsing

**Use Cases:**
- Quick credential lookup for specific people
- Finding projects by client, industry, or year
- Exporting filtered results for reports
- Browsing the database without generating presentations

### Page 6: PowerPoint Generator 🤖
**File:** `pages/6_PowerPoint_Generator.py`

**Features:**
- Natural language chat interface
- AI-powered project filtering
- Intelligent project selection (most recent + diverse)
- Dynamic description generation with AI
- Automatic PowerPoint template filling
- Interactive conversational flow

**Conversation Flow:**
1. Request: "Fill template with [Name]"
2. Filter: "Only 2024-2025" or "skip"
3. Count: "5 projects"
4. Details: "yes" for AI descriptions
5. Download PowerPoint ✅

**Example Commands:**
```
Fill in the template with Bud van der Schier's most recent experience
Generate credentials for Tim Kramer
I need Charbel Moussa's latest project credentials
```

## 📦 Files Added

```
room_allocator_strategy_2/
├── pages/
│   ├── 5_Credential_Browser.py      # Browse credentials
│   └── 6_PowerPoint_Generator.py    # Generate PowerPoint with AI
├── Bud van der Schier– Partner.pptx # PowerPoint template
└── credentials_full.xlsx            # Database (already exists)
```

## 🔧 Dependencies

Updated `requirements.txt` to include:
- `python-pptx>=0.6.21` - For PowerPoint generation

All other dependencies were already in the project.

## 🚀 How to Use

### Quick Start:
1. **Launch the app:** `streamlit run app.py` or `./start_local.ps1`
2. **Navigate:** Use sidebar to select Page 5 or Page 6
3. **Credential Browser (Page 5):** Select person → Apply filters → Export
4. **PowerPoint Generator (Page 6):** Type request → Answer questions → Download

### Requirements:
- **For Browsing (Page 5):** Just the Excel database
- **For PowerPoint (Page 6):** KPMG network access (VPN) for AI features

## 📊 Data Requirements

The app uses `credentials_full.xlsx` with these key columns:
- Project name / engagement title
- Client name
- Year of completion
- Industry / Sector
- Service offering / proposition
- Engagement partner / Engagement manager
- Team members
- Credential description

## 🎯 Output Format

PowerPoint bullets are formatted as:
```
• Project Title (Year)
• Project Title (Year) - AI-generated professional description
```

**Example:**
```
• Buy-side commercial due diligence on a flexible packaging player for a private equity player (2022)
• Strategy study on waste-to-materials markets in Europe for a large private equity player (2022) - European recycling market analysis and investment strategy
```

## 🔐 AI Configuration

- Uses KPMG Workbench API (same as Project Database AI Chat)
- Pre-configured with default settings
- Requires KPMG network access (VPN or on-premises)
- No manual setup needed

## 💡 Tips

**For Credential Browser:**
- Use multiselect filters to narrow down results quickly
- Export filtered results for external use
- Search all projects mode is great for client-based queries

**For PowerPoint Generator:**
- Be specific with natural language: "Only financial services 2024-2025"
- Skip filtering for automatic most recent selection
- Choose "yes" for details to get AI-enhanced descriptions
- The AI will select diverse projects across industries/services

## 🆚 Page Comparison

| Feature | Credential Browser (5) | PowerPoint Generator (6) |
|---------|------------------------|--------------------------|
| Search by person | ✅ | ✅ |
| Filter projects | ✅ Manual | ✅ AI-powered |
| Export CSV/Excel | ✅ | ❌ |
| Natural language | ❌ | ✅ |
| Generate PowerPoint | ❌ | ✅ |
| AI descriptions | ❌ | ✅ |
| Requires VPN | ❌ | ✅ |

## 🎨 Navigation

The pages are automatically added to the Streamlit sidebar:
1. Room Allocation (main pages)
2. Project Database (Page 4)
3. **Credential Browser (Page 5)** ← NEW
4. **PowerPoint Generator (Page 6)** ← NEW

## ✨ Benefits

**Integrated Solution:**
- All tools in one application
- Shared database (credentials_full.xlsx)
- Consistent UI/UX
- Single deployment

**No Separate Installation:**
- Everything runs from room_allocator_strategy_2
- Same launch method (`streamlit run app.py`)
- No additional configuration needed

## 📝 Version

**Integration:** November 2025
**Built with:** Streamlit, Python-PPTX, Pandas, GPT-4
**Integrated into:** room_allocator_strategy_2 v2.0+

---

**Ready to use!** Just launch the app and navigate to the new pages. 🎉
