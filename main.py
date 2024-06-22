from llama_index.llms.ollama import Ollama
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex,SimpleDirectoryReader,Prompt
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.tools import QueryEngineTool,ToolMetadata
from llama_index.core.agent import ReActAgent
from dotenv import load_dotenv
from code_reader import code_reader
from prompts import context,code_parser_template
import os
#to finally write the code in a file:
from pydantic import BaseModel
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.query_pipeline import QueryPipeline #allows to combine multiple steps into one
from llama_index.core.prompts import PromptTemplate
#For cleaning the output format 
import ast


load_dotenv()
#we need to load in data and in this case we are loading in the pdf 
#we need to parese the pdf into logical portion in chunks
#after that make the vector store index
#we will store in the vector index by doing vector embedding
llm = Ollama(model="mistral", request_timeout=500.0)  # Increase to 60 seconds

parser=LlamaParse(result_type="markdown")
#llama parse is given by llama index this basically takes the document and push them out to the cloud which will be parsed 
#and then will be returned it back to us
file_extractor={".pdf":parser}
#whenever a .pdf file do parsing
documents=SimpleDirectoryReader("./data",file_extractor=file_extractor).load_data()
#load the data from  the data directory and will apply the file_extractor dependent on the file

embed_model=resolve_embed_model("local:BAAI/bge-m3")
#here we are using local model to do that ,(default is open ai)
vector_index=VectorStoreIndex.from_documents(documents, embed_model=embed_model)
query_engine=vector_index.as_query_engine(llm=llm)
#so what it does is that we can utilize the vectorindex as the question answer bot
#result=query_engine.query("what are some of the routes in the api??")
#print(result)
tools=[
    QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="api_documentation",
            description="This goves documentation about the code for an API.Use this for reading docs for the API",
        ),
    ),
    code_reader,
]
#now we will use another llm to generate the code for us and give it to this agent.
code_llm = Ollama(model="codellama", request_timeout=500.0)
agent = ReActAgent.from_tools(tools, llm=code_llm, verbose=True, context=context)

class CodeOutput(BaseModel):
    #now we define the type of information that we want our output to be parsed into
    #we can use llama index and these output parsers to actually convert a result from an llm into a pydantic object
    #so we can specify the type that we want in the pydantic object 
    #and then llama index and another llm can actually format the result to match this pydantic obejct
    code:str
    description:str
    filename:str

parser=PydanticOutputParser(CodeOutput)
json_prompt_str=parser.format(code_parser_template)#sp here the code description and filename is injected to the output, it will give format to the string
json_prompt_tmpl=PromptTemplate(json_prompt_str)#we write a kind of a wrapper on the prompt template so we can actually inject insde of here response
output_pipeline=QueryPipeline(chain=[json_prompt_tmpl,llm])

#now the output pipline is ready now we will take the output pipeline and we want to pass this result ot it 
#and then we will get a result back, whihc is gonna be the formatted obhect that we want to look at

while(prompt :=input("Enter a prompt(q to quit):")) !="q":
    
    retries=0
    while retries<3:
        try:
            result=agent.query(prompt)
            next_result=output_pipeline.run(response=result)
            #print(next_result) so here we are getting the ouptut which is unclean so now we make it better
            cleaned_json=ast.literal_eval(str(next_result).replace("assistant:",""))
            #so all we are doing here is removing that assistant that came before that valid python dictionary 
            #and then we are loading in the rest of this as  a python dictionary object.
            break
        except Exception as e:
            retries+=1
            print("error occured ,retry#{retries}:",e)
    if retries>=3:
        print("Unable to process request, try again....")
        continue
    
    print("code generated")
    print(cleaned_json["code"])
    
    print("\n\nDescription:",cleaned_json["description"])
    filename=cleaned_json["filename"]
    
    try:
        with open(os.path.join("output",filename),"w") as f:
            f.write(cleaned_json["code"])
        print("saved file",filename)
    except:
        print("Error saving file")