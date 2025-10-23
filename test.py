from services.analysis_service import analysis
from services.llm_service import feedback_list_analysis, generate_topics_list, topics_analysis

if __name__ == "__main__":
    print(topics_analysis(feedback_list_analysis()))
