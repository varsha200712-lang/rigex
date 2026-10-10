"""
Custom CSS and visual design system for ResolveAI.
Color Palette:
- Primary: Deep Emerald (#064E3B, #047857)
- Light Accent: Pale Mint Green (#ECFDF5, #D1FAE5)
- Secondary Accents: Sky Blue (#E0F2FE, #0284C7), Soft Lavender (#F3E8FF, #7E22CE), Coral (#FFE4E6, #E11D48)
- Background: Clean off-white (#F8FAFC)
- Typography: Inter, -apple-system, BlinkMacSystemFont, Segoe UI
"""

CUSTOM_CSS = """
<style>
/* Global Imports & Reset */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1E293B;
}

/* Background refinement */
.stApp {
    background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
}

/* Header & Banner */
.brand-header {
    background: linear-gradient(135deg, #064E3B 0%, #065F46 50%, #047857 100%);
    padding: 1.5rem 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 25px -5px rgba(6, 78, 59, 0.2);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.brand-title {
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.brand-badge {
    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Metric Cards */
.metric-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.25rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #064E3B;
    margin: 0.3rem 0;
    letter-spacing: -0.03em;
}
.metric-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.metric-change {
    font-size: 0.8rem;
    font-weight: 500;
    color: #059669;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

/* Status Badges */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.badge-processing { background: #FEF3C7; color: #92400E; }
.badge-shipped { background: #E0F2FE; color: #0369A1; }
.badge-intransit { background: #EDE9FE; color: #6D28D9; }
.badge-delivered { background: #D1FAE5; color: #065F46; }
.badge-delayed { background: #FEE2E2; color: #991B1B; }
.badge-cancelled { background: #F1F5F9; color: #475569; }

.badge-low { background: #F1F5F9; color: #475569; }
.badge-medium { background: #E0F2FE; color: #0369A1; }
.badge-high { background: #FEF3C7; color: #92400E; }
.badge-urgent { background: #FEE2E2; color: #991B1B; }

/* Chat Elements */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.chat-bubble-user {
    align-self: flex-end;
    background: linear-gradient(135deg, #064E3B 0%, #047857 100%);
    color: white;
    padding: 0.9rem 1.25rem;
    border-radius: 18px 18px 4px 18px;
    max-width: 80%;
    box-shadow: 0 4px 10px rgba(6, 78, 59, 0.15);
    font-size: 0.95rem;
    line-height: 1.5;
}
.chat-bubble-ai {
    align-self: flex-start;
    background: white;
    color: #1E293B;
    padding: 1.1rem 1.4rem;
    border-radius: 18px 18px 18px 4px;
    max-width: 85%;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    font-size: 0.95rem;
    line-height: 1.55;
}
.chat-step-pill {
    display: inline-flex;
    align-items: center;
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    color: #065F46;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.2rem 0.5rem;
    border-radius: 6px;
    margin-right: 0.4rem;
    margin-top: 0.4rem;
}

/* Quick Action Prompt Cards */
.quick-prompt-card {
    background: white;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
    height: 100%;
}
.quick-prompt-card:hover {
    border-color: #059669;
    background: #F0FDF4;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(5, 150, 105, 0.1);
}

/* Agent Monitor Cards */
.agent-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.4rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.agent-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #F1F5F9;
    padding-bottom: 0.75rem;
    margin-bottom: 0.85rem;
}
.agent-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0F172A;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.agent-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10B981;
    display: inline-block;
}

/* Order timeline */
.timeline-stepper {
    display: flex;
    justify-content: space-between;
    position: relative;
    margin: 1.5rem 0;
}
.timeline-stepper::before {
    content: '';
    position: absolute;
    top: 14px;
    left: 20px;
    right: 20px;
    height: 3px;
    background: #E2E8F0;
    z-index: 1;
}
.timeline-step {
    position: relative;
    z-index: 2;
    text-align: center;
}
.step-circle {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: white;
    border: 3px solid #CBD5E1;
    margin: 0 auto 0.4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
}
.step-circle.active {
    border-color: #059669;
    background: #059669;
    color: white;
}
.step-circle.done {
    border-color: #059669;
    background: #ECFDF5;
    color: #059669;
}
.step-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #475569;
}

/* Sidebar styling override */
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}
</style>
"""
