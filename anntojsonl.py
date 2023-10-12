import os
import re
import json

directory_old = "../test_data/chia_without_scope"
directory_new = "./reduced_chia_dataset"
binarize_non_binary_relations = False

entity_counter = 0
relation_counter = 0
global_sentence_counter = 0

def sentence_to_tokenlist(sentence):
    """ :param sentence: string
        :return: tokenlist (list of strings)
        
        splits a sentence into tokens
        returns a list of tokens
    """
    sentence = sentence.replace("-", " - ")
    sentence = sentence.replace(",", " , ")
    sentence = sentence.replace(";", " ; ")
    sentence = sentence.replace(".\n", " .")
    sentence = sentence.replace("[", " [ ")
    sentence = sentence.replace("]", " ] ")
    sentence = sentence.replace("(", " ( ")
    sentence = sentence.replace(")", " ) ")
    sentence = sentence.replace("/", " / ")
    sentence = sentence.replace("'", " '")
    sentence = sentence.replace(".", " . ")
    sentence = sentence.replace(":", " : ")
    sentence = sentence.replace("\n", "")
    sentence = sentence.replace("=", " = ")
    sentence = sentence.replace("%", " % ")
    sentence = sentence.replace(">", " > ")
    sentence = sentence.replace("<", " < ")
    sentence = sentence.replace("*", " * ")
    sentence = sentence.replace("\"", " \" ")
    special_chars = ["-", ",", ";", ".", "\n", "[", "]", "(", ")", "/", "'", ":", " ", "=",
                     "%", "<", ">", "*", "\""]

    old_char = '\0'

    for s in sentence:
        if not s.isalnum() and s not in special_chars :
            sentence = sentence.replace(s, " " + s + " ")
        # check if word contains numbers AND characters, if so: split
        if s.isalpha() and old_char.isnumeric() or s.isnumeric() and old_char.isalpha():
            sentence = sentence.replace(old_char + s, old_char + " " + s)
        old_char = s
        
    tokenlist = sentence.split(" ")
    tokenlist = filter(lambda token: token != "", tokenlist)
    return list(tokenlist)



def file_to_sentences(file):
    """ :param file: string, path of file not opened yet
        :return: sentences (list of strings)
        
        reads the lines of a file, interprets each line as one sentence
        removes the newline in each sentence
        returns a list of sentences
    """
    with open(file, "r") as file:
        sentences = file.readlines()

    for i in range(len(sentences)):
        sentences[i] = sentences[i].replace("\n", "")

    return sentences



def tokenlist_to_dictlist(tokenlist, sentence):
    """ :param tokenlist: list of strings, list of tokens from the sentence
        :param sentence: string
        :return: dictlist (list of dictionaries)
        
        gives each token from the tokenlist from the sentence the needed attributes, like starting point, end point, etc
        returns a list of dictionaries, containg each token of the input sentence with the needed attributes
    """
    dictlist = []

    char_index = 0  # the character index of the token (first char of token) in the sentence
    id = 0          # each token gets an id, the token-index in the sentence

    for token in tokenlist:
        dict = {}
        dict["text"] = token
        dict["start"] = char_index
        dict["end"] = char_index + len(token)
        dict["id"] = id
        dict["ws"] = True
        # ws = whitespace, is True if the token follows a whitespace in the sentence
        if sentence[dict["end"]] != " ":
            dict["ws"] = False

        dictlist.append(dict)
        id += 1
        if dict["ws"]:
            char_index += len(token) + 1
        else:
            char_index += len(token)
    return dictlist



def create_entities_and_relations(txtfile, annfile):
    """ :param txtfile: string, path of text-file not opened yet
        :param annfile: string , path of ann-file not opened yet
        :return: (entities, relations) (tuple of two lists, each list contains lists of dictionaries)
        
        creates a dictionary for each entity and relation, containing the needed attributes
        assigns each entity and relation specified in the annfile to a corresponding list
        each list is for one sentence in the txtfile

        returns tuple of the entity-list and the relation-list
        each list contains one list for each sentence, that contains all entities or relations of that sentence
    """
    bytefile = open(txtfile, "rb")                      # open in byte mode, to compute length of sentence correctly (avoid index problem with windows newline \r\n)
    txtfile = open(txtfile, "r")


    ann_entities = []
    ann_relations = []
    # split the entities and relations specified in the annfile into two lists (ann_entities, ann_relations)
    with open(annfile, "r") as annfile:
        for line in annfile.readlines():
            if line[0] == "T":                          # line specifies an entity
                line = re.split(r" |\t", line, 4)       # keep the content of the entity (4th column) complete and don't split it
                ann_entities.append(line)
            elif line[0] == "R" or line[0] == "*":      # line specifies a relation
                line = re.split(r" |\t", line)
                if len(line) <= 5:
                    ann_relations.append(line[:4])      # add relation to the list, only take the first 4 columns, the last one only contains a \t

    # sort entities by occurence in the txtfile (each startindex, specified in 2nd column of the annfile)
    def sort_key(x):
        return int(x[2])
    ann_entities.sort(key = sort_key)
    
    # this list is needed to assign the entities to the relations later (the relations in the annfile only contain the identifier from the entity specified in the annfile)
    entity_identifier_list = []

    # the final entity-list
    entities = []
    sentence = txtfile.readline()
    sentence_byte = bytefile.readline() # to compute sentence length correctly (check if txtfile was generated in windows and contains a \r\n instead of \n)
    sen_len = len(sentence)             # current sentence length, needed to compute the index of each entity. each sentence has to start with 0. in the annfile only the first sentence starts with 0
    if b'\r' in sentence_byte:
        sen_len += 1
    char_counter = 0                    # global character counter in the txtfile. needed to compute the index of each entity
    sentence_counter = 0
    entities_from_one_sentence = []

    # skip empty lines at the beginning of the file
    while sentence.replace(" ", "").replace("\t", "") == "\n":
        char_counter += sen_len
        sentence = txtfile.readline()
        sentence_byte = bytefile.readline()
        sen_len = len(sentence)
        if b'\r' in sentence_byte:
            sen_len += 1

    for entity in ann_entities:
        # remove newlines from entity and change end index accordingly (-1 if \n was annotated)
        entity[4] = entity[4].replace("\n", "")
        if int(entity[3]) - int(entity[2]) != len(entity[4]):
            entity[3] = str(int(entity[3]) - 1)
            if int(entity[3]) - int(entity[2]) != len(entity[4]):
                print("error (indizes of the entity don't match the actual length). Use pdb to find the reason, have fun!")
                import pdb; pdb.set_trace()
        # if the entity doesn't belong to the current sentence, create a new list and add the old one to the final entity list
        # add empty lists of entities to the final list, if sentences don't have any entities
        while int(entity[2]) >= char_counter + sen_len:                    # start index of the entity isn't inside the current sentence
            if len(sentence.replace(" ", "").replace("\t", "")) > 1:       # skip empty lines in txtfile
                sentence_counter += 1
                entities.append(entities_from_one_sentence)
                entities_from_one_sentence = []
            char_counter += sen_len
            sentence = txtfile.readline()
            sentence_byte = bytefile.readline()
            sen_len = len(sentence)
            if b'\r' in sentence_byte:
                sen_len += 1

        # get start and end index of entity (by counting characters in the sentence)
        entity_start_index = int(entity[2]) - char_counter
        if entity_start_index < 0:
            print("error: entity_start_index smaller than zero in " + str(txtfile))
        entity_end_index = int(entity[3]) - char_counter
        if entity_end_index < 0:
            print("error: entity_end_index smaller than zero in " + str(txtfile))

        # find token (current entity) position in current sentence
        def find_token_position():
            sentence_tokenlist_with_indices = sentence_to_tokenlist(sentence)
            # give each token an token-index
            for i in range(len(sentence_tokenlist_with_indices)):
                sentence_tokenlist_with_indices[i] = (sentence_tokenlist_with_indices[i], i)
            sentence_cut = sentence[entity_start_index:]
            sentence_cut_tokenlist = sentence_to_tokenlist(sentence_cut)
            entity_token_start_index = -1
            # find index of entity by searching for the part of the sentence starting with the entity in the sentence_tokenlist_with_indices
            for t in range(len(sentence_tokenlist_with_indices)):
                try:
                    b = sentence_cut_tokenlist[0]
                except:
                    print("error: turning on pdb: ")
                    import pdb; pdb.set_trace()
                if sentence_cut_tokenlist[0] in sentence_tokenlist_with_indices[t][0]:              # not ==, in case the first word of the entity wasn't annotated completely
                    for i in range(len(sentence_cut_tokenlist)):
                        try:
                            if sentence_tokenlist_with_indices[t + i][0] != sentence_cut_tokenlist[i] and i != 0:
                                break
                            elif t + i == len(sentence_tokenlist_with_indices) - 1:                 # found entity token index
                                entity_token_start_index = sentence_tokenlist_with_indices[t][1]
                                break
                        except:
                            import pdb; pdb.set_trace()
                if entity_token_start_index != -1:
                    break
            return entity_token_start_index

        # get start and end token index of the entity (counting tokens in the sentence)
        entity_text_tokenlist = sentence_to_tokenlist(entity[4])
        token_start = find_token_position()
        token_end = token_start + len(entity_text_tokenlist) - 1
        if token_start < 0:
            print("error: There's something wrong in " + annfile)
            print("entity wasn't found in sentence or index was computed wrong")
            import pdb; pdb.set_trace()
        # correct incomplete annotations
        else:
            tmp_sen = sentence_to_tokenlist(sentence)
            tmp_en = sentence_to_tokenlist(entity[4])
            if tmp_sen[token_start] != tmp_en[0] or tmp_sen[token_end] != tmp_en[-1]:
                start_diff = 0
                end_diff = 0
                # find how many characters are missing at the beginning of the entity
                for i in range(len(tmp_sen[token_start])):
                    if tmp_en[0] in tmp_sen[token_start][i:]:
                        if i > 0:
                            start_diff += 1
                    else:
                        break

                # find how many characters are missing at the end of the entity
                for i in range(len(tmp_sen[token_end])):
                    if tmp_en[-1] in tmp_sen[token_end][:len(tmp_sen[token_end]) - 1 - i]:
                        end_diff += 1
                    else:
                        break

                entity_start_index -= start_diff
                entity_end_index += end_diff
                entity[4] = sentence[entity_start_index:entity_end_index]
                if entity_start_index < 0 or entity_end_index < 0:
                    print("error: something went wrong while correcting incomplete annotation of entity in " + annfile)
                    import pdb; pdb.set_trace()

        dict = {}
        dict["text"] = entity[4]
        dict["start"] = entity_start_index
        dict["token_start"] = token_start
        dict["token_end"] = token_end
        dict["end"] = entity_end_index
        dict["type"] = "span"
        dict["label"] = entity[1]

        entities_from_one_sentence.append(dict)
        global entity_counter
        entity_counter += 1
        entity_identifier_list.append((entity[0], entity_start_index, entity_end_index, token_start, token_end, entity[1], sentence_counter))
    entities.append(entities_from_one_sentence)

    # add empty lists of entities for all sentences at the end of the document without entities
    sentence = txtfile.readline()
    while sentence:
        if len(sentence.replace(" ", "").replace("\t", "")) > 1:           # skip empty lines
            entities_from_one_sentence = []
            entities.append(entities_from_one_sentence)
        sentence = txtfile.readline()

    # the final relation list
    relations = []

    # find the entity of a relation in a list of entities by searching for the entity identifier specified in the annfile
    def find_entity(e_identifier, list):
        for l in list:
            if l[0] == e_identifier:
                return l
            
    sen_counter = 0         # counter for the number of lists (each list for one sentence, containing the relations of that sentence)
    for relation in ann_relations:
        e1 = relation[2].replace("Arg1:", "").replace("\n", "")
        e1 = find_entity(e1, entity_identifier_list)
        e2 = relation[3].replace("Arg2:", "").replace("\n", "")
        e2 = find_entity(e2, entity_identifier_list)

        dict = {}
        # start of the arrow (relation), arg1 of relation
        try:
            dict["head"] = e1[4]            # token_end of arg1
        # arrowhead (relation), arg2 of relation
            dict["child"] = e2[4]           # token_end of arg2
        except:
            import pdb; pdb.set_trace()
        dict["head_span"] = {
            "start": e1[1],
            "end": e1[2],
            "token_start": e1[3],
            "token_end": e1[4],
            "label" : e1[5]
        }
        dict["child_span"] = {
            "start": e2[1],
            "end": e2[2],
            "token_start": e2[3],
            "token_end": e2[4],
            "label" : e2[5]
        }
        dict["label"] = relation[1]

        # add relation to the list of the corresponding sentence
        # if list doesn't exist yet, create lists until the n-th (specified in e1[6]) list is created
        try:
            relations[e1[6]].append(dict)
            global relation_counter
            relation_counter += 1
        except IndexError:            
            while e1[6] >= sen_counter:
                sen_counter += 1
                relations.append([])
            relation_counter += 1
            relations[e1[6]].append(dict)

    # add empty lists of relations for all sentences at the end of the document without relations
    while len(relations) < len(entities):
        relations.append([])

    txtfile.close()
    return (entities, relations)


def remove_empty_sentences(sentences):
    """
    :param sentences: list of strings
    :return: list of strings

    removes all empty sentences from a list of sentences
    """
    out = []

    for sentence in sentences:
        if len(sentence.replace(" ", "").replace("\t", "")) > 1:  
            out.append(sentence.replace("\n", ""))

    return out



def main():
    with open("./data.jsonl", "w+") as outfile:
        # go through all files in directory
        for file in os.listdir(directory_new):
            filename = os.path.join(directory_new, file)
            # for each ann-file get the txt-file and read all lines/sentences
            if filename.endswith(".ann") and os.path.isfile(filename):
                txtfile = filename.replace(".ann", ".txt")
                sentences = file_to_sentences(txtfile)
                sentences = remove_empty_sentences(sentences)
                # get entity- and relation-lists (one entity-list and one relation-list for each sentence)
                entities, relations = create_entities_and_relations(txtfile, filename)
                counter = 0         # to give each sentence the correct entity- and relation-list
                # create a dictionary for each sentence and parse to json, write to output-file
                for sentence in sentences:
                    if len(sentence) > 1:
                        sentence += "\n"
                        jsonldict = {}
                        jsonldict["text"] = sentence
                        jsonldict["spans"] = entities[counter]
                        jsonldict["meta"] = {"source": txtfile}
                        # split each sentence into tokens with attributes
                        jsonldict["tokens"] = tokenlist_to_dictlist(sentence_to_tokenlist(sentence), sentence)
                        jsonldict["relations"] = relations[counter]
                        jsonldict["answer"] = "accept"
                        json.dump(jsonldict, outfile)
                        global global_sentence_counter
                        global_sentence_counter += 1
                        outfile.write("\n")
                        counter += 1


def isoverlapping(list_of_entities, entity):
    """
    :param list_of_entities: list of entities to compare with the entity
    :param entity: first, second and third column of entity in .ann-file (identifier, start-index, end-index)
    :return: overlapping (boolean) and the entity that overlaps

    check if the entity overlaps with another entity of the given list (by comparing their indices)
    """
    overlapping = []
    for e in list_of_entities:
        if entity[1] == e[1] or entity[1] == e[2] or (int(entity[1]) > int(e[1]) and int(entity[1]) < int(e[2])):
            overlapping.append(e)
        elif entity[2] == e[1] or entity[2] == e[2] or (int(entity[2]) > int(e[1]) and int(entity[2]) < int(e[2])):
            overlapping.append(e)
        elif int(e[1]) > int(entity[1]) and int(e[1]) < int(entity[2]):
            overlapping.append(e)
        elif int(e[2]) > int(entity[1]) and int(e[2]) < int(entity[2]):
            overlapping.append(e)
    if len(overlapping) > 0:
        return True, overlapping
    else:
        return False, None



def clean_chia_daten():
    """
    removes all non-continous entities
    removes all relations between entities, that are non-continous
    """
    removed_noncontinous_entity_counter = 0
    removed_overlapping_entity_counter = 0
    removed_relation_counter = 0
    remove_relation_noncontinous = 0
    remove_relation_overlapping = 0
    remove_relation_beides = 0
    saved_relations = 0
    binarized_relations = 0
    non_bin_rels = 0
    relations = 0
    remove_non_binary_relations = 0

    try:
        os.mkdir(directory_new)
    except:
        print("Folder already exists. It won't be created again.")

    for file in os.listdir(directory_old):
        file_old = os.path.join(directory_old, file)
        file_new = os.path.join(directory_new, file)
        if file_old.endswith(".ann") and os.path.isfile(file_old):
            list_discontinous_entities = []         # identifier of entities that are discontinous
            list_overlapping_entities = []          # identifier and indices of entities that are overlapping with other entities
            list_good_entities = []                 # identifier and indices of entities that are continous and non-overlapping
            list_ents_in_relations = []
            # create a list with all entities that have a relationship
            with open(file_old, "r") as read:
                line = read.readline()
                while line:
                    cols = re.split(r" |\t", line)
                    if (line[0] == "R" and len(cols) <= 5) or (line[0] == "*" and len(cols) <= 4):
                        e1 = cols[2].replace("Arg1:", "").replace("\n", "")
                        e2 = cols[3].replace("Arg2:", "").replace("\n", "")
                        if e1 not in list_ents_in_relations:
                            list_ents_in_relations.append(e1)
                        if e2 not in list_ents_in_relations:
                            list_ents_in_relations.append(e2)
                    elif line[0] == "R" or line[0] == "*":
                        for i in range(2, len(cols)):
                            e = cols[i].replace("\n", "")
                            if e not in list_ents_in_relations:
                                list_ents_in_relations.append(e)
                    line = read.readline()
            # find all non-continous and overlapping entities and save them in lists
            with open(file_old, "r") as read:
                line = read.readline()
                while line:
                    if line[0] == "T":
                        cols = re.split(r" |\t", line)
                        # if entity is non-continous
                        if ";" in cols[3]:
                            list_discontinous_entities.append(cols[0])
                            removed_noncontinous_entity_counter += 1
                        # if entity overlaps with another entity
                        elif isoverlapping(list_good_entities, (cols[0], cols[2], cols[3]))[0]:# or isoverlapping(list_good_entities, (cols[0], cols[2], cols[3])):
                            overlap_ents = isoverlapping(list_good_entities, (cols[0], cols[2], cols[3]))[1]
                            for overlap_ent in overlap_ents:
                                if overlap_ent[0] in list_ents_in_relations and overlap_ent in list_good_entities:
                                    list_overlapping_entities.append((cols[0], cols[2], cols[3]))
                                    removed_overlapping_entity_counter += 1
                                elif cols[0] not in list_ents_in_relations:
                                    list_overlapping_entities.append((cols[0], cols[2], cols[3]))
                                    removed_overlapping_entity_counter += 1
                                else:
                                    if overlap_ent in list_good_entities:
                                        list_good_entities.remove(overlap_ent)
                                        list_overlapping_entities.append(overlap_ent)
                                        removed_overlapping_entity_counter += 1
                            if isoverlapping(list_good_entities, (cols[0], cols[2], cols[3]))[0]:
                                list_overlapping_entities.append((cols[0], cols[2], cols[3]))
                                removed_overlapping_entity_counter += 1
                            else:
                                list_good_entities.append((cols[0], cols[2], cols[3]))
                        else:
                            list_good_entities.append((cols[0], cols[2], cols[3]))
                    line = read.readline()

            list_good_entities = [i[0] for i in list_good_entities]
            list_overlapping_entities = [i[0] for i in list_overlapping_entities]

            # delete all found entities and corresponding relations
            # only keep relations with 2 arguments
            with open(file_old, "r") as read, open(file_new, "w+") as write:
                line = read.readline()
                while line:
                    cols = re.split(r" |\t", line)
                    if cols[0] in list_good_entities:
                        write.write(line)
                    elif (line[0] == "R" and len(cols) <= 5) or (line[0] == "*" and len(cols) <= 4):
                        e1 = cols[2].replace("Arg1:", "").replace("\n", "")
                        e2 = cols[3].replace("Arg2:", "").replace("\n", "")
                        if e1 in list_good_entities and e2 in list_good_entities:
                            write.write(line)
                            relations += 1
                        else:
                            if e1 in list_overlapping_entities and e2 not in list_discontinous_entities:
                                remove_relation_overlapping += 1
                            elif e2 in list_overlapping_entities and e1 not in list_discontinous_entities:
                                remove_relation_overlapping += 1
                            elif e1 in list_discontinous_entities and e2 not in list_overlapping_entities:
                                remove_relation_noncontinous += 1
                            elif e2 in list_discontinous_entities and e1 not in list_overlapping_entities:
                                remove_relation_noncontinous += 1
                            else:                            
                                remove_relation_beides += 1
                    else:
                        # binarize non-binary relations
                        if line[0] == "R" or line[0] == "*":
                            if binarize_non_binary_relations:
                                non_bin_rels += 1
                                es = cols[2:]
                                es[-1] = es[-1].replace("\n", "")
                                binarized_relations += len([(x, y) for x in es for y in es if x < y])
                                for e1, e2 in [(x, y) for x in es for y in es if x < y]:
                                    if e1 != e2 and e1 in list_good_entities and e2 in list_good_entities:
                                        write.write(cols[0] + "\t" + cols[1] + " " + e1 + " " + e2 + "\n")
                                        relations += 1
                                        saved_relations += 1
                                    else:
                                        removed_relation_counter += 1
                            else:
                                remove_non_binary_relations += 1
                        elif line[0] != "\n" and line[0] != "*" and cols[0] not in list_discontinous_entities and cols[0] not in list_overlapping_entities:
                            import pdb; pdb.set_trace()

                    line = read.readline()
        elif file_old.endswith(".txt") and os.path.isfile(file_old):
            os.system("cp " + file_old + " " + directory_new)
    print("how many relations had to be removed due to overlapping or non-continous entities (or because they were non-binary if boolean was set so (or because they were binarized but had be removed anyway)): " + str(remove_relation_noncontinous + remove_relation_overlapping + remove_relation_beides + removed_relation_counter + remove_non_binary_relations))
    print("how many relations got parsed: " + str(relations))
    
    return (removed_noncontinous_entity_counter, removed_overlapping_entity_counter)



if __name__ == "__main__":
    (noncont, overlap) = clean_chia_daten()
    print("removed non-continous entities: " + str(noncont))
    print("removed overlapping entities: " + str(overlap))
    main()
    print("parsed entities: " + str(entity_counter))
    print("parsed relations: " + str(relation_counter))
    print("parsed sentences: " + str(global_sentence_counter))