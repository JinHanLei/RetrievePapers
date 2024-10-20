import pandas as pd
from tqdm import tqdm
import openai
import backoff


client = openai.OpenAI(
    api_key="None",
)


@backoff.on_exception(backoff.expo, openai.RateLimitError)
def completions_with_backoff(**kwargs):
    return client.chat.completions.create(**kwargs)


def query_builder(title, abstract):
    return "title: '{}'\nabstract: '{}'\n".format(title, abstract)


def classify_papers(test, train, task, prompt):
    if not task in test.columns:
        test[task] = None
    history = [{"role": "system", "content": prompt}]
    if train is not None:
        for i in range(len(train)):
            history += ([{"role": "user", "content": query_builder(train["title"][i], train["abstract"][i])},
                         {"role": "assistant", "content": str(train[task][i])}])
    for i in tqdm(range(len(test))):
        if pd.isna(test[task][i]):
            try:
                messages = history + [{"role": "user", "content": query_builder(test["title"][i], test["abstract"][i])}]
                # chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
                chat = completions_with_backoff(model="gpt-3.5-turbo", messages=messages)
                label = chat.choices[0].message.content
            except Exception as e:
                label = None
                print(e)
            test.loc[i, task] = label
    return test


if __name__ == '__main__':

    PREFIX = "You are an expert in NLP. Please classify the article according to its title and abstract. "
    PROMPT = {
        "isLLM": "Please classify the articles related to Large Language Models (LLMs). Mark them as 0 if they are not related to Large Language Models (LLMs); if they are related to LLMs, specify which LLM is used in the article, such as T5, BART, GPT-3, ChatGPT, or LLAMA. ",
        "task": "The task include test, survey, dataset, model, etc. ",
        "model": "If the article directly uses basic large language models please indicate the model directly, such as ChatGPT or Llama. If it is a self built model, please findout its name. If multiple models are used, please list them all. ",
        "mechanism": "The mechanisms include prompt, fine-tuning, training, distillation, etc. ",
        "domain": "If no specific domain is specified and it only indicates summarization task, then mark it as general. If specific fields are mentioned, including medical, dialogue, law, news, etc., please indicate the domain name. ",
        "dataset": "Please list all the datasets used in this paper. If not found, please output 0"
    }
    SUFFIX = "No need for explanation."

    sum_train = pd.read_csv(f"LLM_train.csv")
    sum_test = pd.read_csv("summarization_all_final.csv")

    for task in PROMPT:
        prompt = PREFIX + PROMPT[task] + SUFFIX
        if task not in sum_train.columns:
            prompt += f"Just output {task}. "
            sum_test = classify_papers(sum_test, None, task, prompt)
        else:
            sum_test = classify_papers(sum_test, sum_train, task, prompt)
    sum_test.to_csv("summarization_all_final.csv", index=False)
