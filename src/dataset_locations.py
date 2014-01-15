import json
import subprocess
from time import sleep

JSON_output_file = 'files/dataset_locations.json'
dataset_output_file = 'files/datasets.txt'

def ask_das(query):
    command = './src/das_client.py --query="%s" --format=json' % query
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read()
    
    return result

def get_datasets_from_wildcard(wildcard):
    query = "dataset dataset=%s | grep dataset.name" % wildcard
    result = ask_das(query)
    dic = json.loads(result)
    datasets = []
    add_dataset = datasets.append
    for item in dic['data']:
        for dataset in item['dataset']:
            add_dataset(dataset['name'])
    # remove duplicates and sort
    datasets = sorted(set(datasets))
    
    return datasets, result

def get_dataset_locations(dataset):
    # site dataset=<dataset> | grep site.name
    query = 'site dataset=%s | grep site.name' % dataset
    result = ask_das(query)
    sites = []
    add_site = sites.append
    dic = json.loads(result)
    for item in dic['data']:
        for site in item['site']:
            add_site(site['name'])
    # remove duplicates and sort
    sites = sorted(set(sites))
    # some datasets have the location UNKNOWN. Remove it
    if 'UNKNOWN' in sites:
        sites.remove('UNKNOWN')
    
    return sites

def find_T2_duplicates(dataset_locations_json):
    input_file = open(dataset_locations_json)
    input_JSON = ''.join(input_file.readlines())
    data = json.loads(input_JSON)
    input_file.close()
    
    duplicates = []
    for dataset, sites in data.iteritems():
        number_of_T2_sites = 0
        for site in sites:
            if 'T2' in site:
                number_of_T2_sites += 1
                
        if number_of_T2_sites > 1:
            duplicates.append(dataset)
            
    return duplicates
    
    
def main(input_file='files/test_datasets.txt'):
    datasets = []
    add_dataset = datasets.append
    # get input file
    with open(input_file) as f:
        for line in f:
            if '*' in line:
                line = line.strip('\n')
                print 'Looking for', line
                # if wildcard, first get all datasets
                more_datasets, result = get_datasets_from_wildcard(line)
                if not more_datasets:
                    print result
                print 'Found', more_datasets
                datasets.extend(more_datasets)
            else:
                line = line.strip('\n')
                add_dataset(line)
    
    output_file = open(dataset_output_file, 'w')
    prepared_datasets = [dataset + '\n' for dataset in datasets]
    output_file.writelines(prepared_datasets)
    output_file.close()
    
    output = {}
    
    # ask das_client for locations of every dataset
    for dataset in datasets:
        print 'Probing location of dataset', dataset
        sites = get_dataset_locations(dataset)
        print 'Found locations:', sites
        output[dataset] = sites
        sleep(2)
    
    # create JSON {<dataset>: [<site1>, <site2>]}
    output_file = open(JSON_output_file, 'w')
    output_file.write(json.dumps(output, indent=4, sort_keys=True))
    output_file.close()    


# you can first run with wildcards to get a complete list
# input_file = 'files/datasets_with_wildcards.txt'
input_file = dataset_output_file
main(input_file)

T2_duplicates = find_T2_duplicates(JSON_output_file)
print '='*80
print 'The following samples are available on more than one T2'
print '='*80
for i in T2_duplicates:
    print i
    
output_file = open('files/T2_duplicates.txt', 'w')
for i in T2_duplicates:
    print>>output_file, i
output_file.close()




