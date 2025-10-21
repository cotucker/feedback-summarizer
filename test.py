from services.analysis_service import analysis
from services.llm_service import feedback_list_analysis

if __name__ == "__main__":
    feedback_list = [
        "Their customer support for a minor billing issue was absolutely abysmal. Took 4 different transfers and two weeks to resolve.",
        "Salesforce's CRM platform is indispensable for our sales team, but the cost of add-ons quickly spirals out of control.",
        "The cloud infrastructure rollout was flawless. Zero downtime and everything scaled perfectly on day one. A true enterprise solution."
    ]
    feedback_list_analysis(feedback_list)
