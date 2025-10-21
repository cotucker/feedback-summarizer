from services.analysis_service import analysis
from services.llm_service import feedback_list_analysis, generate_topics_list

if __name__ == "__main__":
    print(feedback_list_analysis(''))
