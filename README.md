# Parser-ann-to-jsonl
## What does the parser do
The parser converts .ann-files, that are created by the [brat annotation tool](https://brat.nlplab.org/introduction.html), to .jsonl-format (JSON Lines). This format can be used for further processing. For example if you want to train some models with [SpaCy](https://spacy.io/usage/spacy-101) you can use their Python-script [parse_data.py](https://github.com/explosion/projects/blob/v3/tutorials/rel_component/scripts/parse_data.py) to convert your data in jsonl-format to .spacy-format. You just have to change the `SYM_LABELS`, `MAP_LABELS` and the way the data is split into train, test, dev.

The parser converts your annotated entities and relations. It doesn't matter if you annotated your text in Windows or not (files annotated in Windows have slightly different indices due to the different byte version of the newline symbol). Non-continous entities will be ignored. When entities overlap, the parser tries to keep and convert the entity that has a relationship and ignores the other one. Every relation that contains an ignored entity will be ignored too. If you have incomplete annotations and missed some characters from a token, it will be corrected by the parser (silently) because SpaCy (and I guess other libraries too) cannot process entities that contain only parts of (a) token(s).

## How to use the parser
1. clone this repository (or just copy the code)
2. change `directory_old` in [anntojsonl.py](anntojsonl.py) to the path where your .txt and .ann files are
3. `directory_new` doesn't have to be changed because it is a temporary directory that will be created while parsing. You can delete it, after the parsing is complete
4. if you have non-binary relations in your annotations and you want them converted into binary relations, change `binarize_non_binary_relations` to `True`. Otherwise they will be ignored and not converted
5. type `python anntojsonl.py` into you command line (or python3 or whatever python version you want to use)
6. the output of the parser are some numbers. For example how many relations were converted/ignored
7. the parsed data is in the created file "data.jsonl"

## Limitations
The parser creates one json dictionary for each line in the .txt-file. So if your annotations contain relations with entities from different lines the parser will throw an error.

If you tamper with your .ann-files and for example change the indices the parser will throw an error.

The parser isn't perfect and there may be other cases I didn't test that lead to errors.

## Example

.txt-file (input)
```txt
I like coding.
My shoe is red.

```

.ann-file (input)
```ann
R1	likes Arg1:T1 Arg2:T2	
R2	has_colour Arg1:T3 Arg2:T4	
T1	Person 0 1	I
T2	activity 7 13	coding
T3	thing 19 23	shoe
T4	colour 27 30	red
```

.jsonl-file (output) (The actual .jsonl file contains two very long lines, each containing one of the JSONs below. I formatted it for better understanding.)
```json
{
    "text": "I like coding.\n",
    "spans": [
        {
            "text": "I",
            "start": 0,
            "token_start": 0,
            "token_end": 0,
            "end": 1,
            "type": "span",
            "label": "Person"
        },
        {
            "text": "coding",
            "start": 7,
            "token_start": 2,
            "token_end": 2,
            "end": 13,
            "type": "span",
            "label": "activity"
        }
    ],
    "meta": {
        "source": "./reduced_chia_dataset/example.txt"
    },
    "tokens": [
        {
            "text": "I",
            "start": 0,
            "end": 1,
            "id": 0,
            "ws": true
        },
        {
            "text": "like",
            "start": 2,
            "end": 6,
            "id": 1,
            "ws": true
        },
        {
            "text": "coding",
            "start": 7,
            "end": 13,
            "id": 2,
            "ws": false
        },
        {
            "text": ".",
            "start": 13,
            "end": 14,
            "id": 3,
            "ws": false
        }
    ],
    "relations": [
        {
            "head": 0,
            "child": 2,
            "head_span": {
                "start": 0,
                "end": 1,
                "token_start": 0,
                "token_end": 0,
                "label": "Person"
            },
            "child_span": {
                "start": 7,
                "end": 13,
                "token_start": 2,
                "token_end": 2,
                "label": "activity"
            },
            "label": "likes"
        }
    ],
    "answer": "accept"
}
{
    "text": "My shoe is red.\n",
    "spans": [
        {
            "text": "shoe",
            "start": 4,
            "token_start": 1,
            "token_end": 1,
            "end": 8,
            "type": "span",
            "label": "thing"
        },
        {
            "text": "red",
            "start": 12,
            "token_start": 3,
            "token_end": 3,
            "end": 15,
            "type": "span",
            "label": "colour"
        }
    ],
    "meta": {
        "source": "./reduced_chia_dataset/example.txt"
    },
    "tokens": [
        {
            "text": "My",
            "start": 0,
            "end": 2,
            "id": 0,
            "ws": true
        },
        {
            "text": "shoe",
            "start": 3,
            "end": 7,
            "id": 1,
            "ws": true
        },
        {
            "text": "is",
            "start": 8,
            "end": 10,
            "id": 2,
            "ws": true
        },
        {
            "text": "red",
            "start": 11,
            "end": 14,
            "id": 3,
            "ws": false
        },
        {
            "text": ".",
            "start": 14,
            "end": 15,
            "id": 4,
            "ws": false
        }
    ],
    "relations": [
        {
            "head": 1,
            "child": 3,
            "head_span": {
                "start": 4,
                "end": 8,
                "token_start": 1,
                "token_end": 1,
                "label": "thing"
            },
            "child_span": {
                "start": 12,
                "end": 15,
                "token_start": 3,
                "token_end": 3,
                "label": "colour"
            },
            "label": "has_colour"
        }
    ],
    "answer": "accept"
}
```