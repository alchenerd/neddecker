from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

describe_hand_chain = prompt | model | output_parser

def main():
    pass

if __name__ == '__main__':
    main()
