# graphrag-dev Algorithm Comparison

## Environment Setup

### Go to root directory of graphrag-dev
```bash
cd ~/home/graphrag-dev
```

### Activate Conda environment
```bash
conda activate rag-dev
```


## Run graphrag index in different cluster algorithms

#### Leiden 
```bash
make run-standard
```

#### EVOC
```bash
make run-evoc
```

#### Louvain
```bash
make run-louvain
``` 

## Query the index

### Use make command to run the query
### Example query
```bash
make query-local QUERY="What is quantum computing?"
```

```bash
make query-global QUERY="What is software engineering?"
```

### Query with command line arguments
```bash
cd ~/home/graphrag-dev/ragtest && \
graphrag query \
  --method standard \
  --query "What is quantum computing?" \
  --data ~/home/graphrag-dev/ragtest/output \
```

You can store output files in a specific directory by adding `--data <your_directory>`.
So you can use output from different cluster methods to compare more easily.