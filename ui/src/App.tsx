import { useState } from 'react';
import {
  Box,
  Container,
  Heading,
  Input,
  Button,
  Text,
  VStack,
  Card,
  CardBody,
  Spinner,
  useToast,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import axios from 'axios';

interface SourceChunk {
  chunk: string;
  filename: string;
  filepath: string;
  chunk_index: number;
  score: number;
}

interface QueryResponse {
  answer: string;
  source_chunks: SourceChunk[];
}

function App() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const toast = useToast();

  const handleSubmit = async () => {
    if (!query.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a query',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post<QueryResponse>('http://localhost:8003/query', {
        question: query,
        top_k: 10,
      });
      setResult(response.data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to get response. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxW="container.lg" py={8}>
      <VStack spacing={6} align="stretch">
        <Heading as="h1" size="xl" textAlign="center">
          RAG Query System
        </Heading>

        <Box>
          <Input
            placeholder="Enter your question..."
            size="lg"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
          />
          <Button
            mt={4}
            colorScheme="blue"
            onClick={handleSubmit}
            isLoading={isLoading}
            width="full"
          >
            Search
          </Button>
        </Box>

        {isLoading && (
          <Box textAlign="center">
            <Spinner size="xl" />
            <Text mt={2}>Processing your query...</Text>
          </Box>
        )}

        {result && !isLoading && (
          <VStack spacing={4} align="stretch">
            <Card>
              <CardBody>
                <Text fontWeight="bold" mb={2}>Answer:</Text>
                <Text whiteSpace="pre-wrap">{result.answer}</Text>
              </CardBody>
            </Card>

            <Accordion allowMultiple>
              <AccordionItem>
                <h2>
                  <AccordionButton>
                    <Box flex="1" textAlign="left">
                      Source Documents
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                </h2>
                <AccordionPanel>
                  <VStack spacing={4} align="stretch">
                    {result.source_chunks.map((chunk, index) => (
                      <Card key={index} variant="outline">
                        <CardBody>
                          <Text fontSize="sm" color="gray.600" mb={2}>
                            File: {chunk.filename}
                          </Text>
                          <Text>{chunk.chunk}</Text>
                        </CardBody>
                      </Card>
                    ))}
                  </VStack>
                </AccordionPanel>
              </AccordionItem>
            </Accordion>
          </VStack>
        )}
      </VStack>
    </Container>
  );
}

export default App;