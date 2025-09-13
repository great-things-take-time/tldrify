"""Semantic text chunking system with intelligent splitting and metadata extraction."""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import tiktoken
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    """Configuration for text chunking."""
    min_tokens: int = 1000
    max_tokens: int = 2000
    overlap_tokens: int = 200
    encoding_model: str = "cl100k_base"  # For text-embedding-3-large
    respect_sentence_boundaries: bool = True
    respect_paragraph_boundaries: bool = True
    detect_structure: bool = True
    enable_deduplication: bool = True


@dataclass
class TextChunk:
    """Represents a single text chunk with metadata."""
    content: str
    chunk_index: int
    token_count: int
    start_char: int
    end_char: int
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    section_title: Optional[str] = None
    chunk_level: int = 0  # 0=main, 1=sub-chunk
    parent_chunk_id: Optional[int] = None
    metadata: Dict[str, Any] = None
    embedding_id: Optional[str] = None
    chunk_hash: Optional[str] = None

    def __post_init__(self):
        """Generate hash for deduplication."""
        if self.chunk_hash is None:
            self.chunk_hash = hashlib.md5(self.content.encode()).hexdigest()
        if self.metadata is None:
            self.metadata = {}


class DocumentStructureExtractor:
    """Extract document structure (chapters, sections, headings)."""

    def __init__(self):
        """Initialize structure patterns."""
        self.heading_patterns = [
            # Chapter patterns
            (r'^Chapter\s+\d+[\s:.-]*(.*)$', 'chapter', 1),
            (r'^CHAPTER\s+\d+[\s:.-]*(.*)$', 'chapter', 1),
            (r'^제\s*\d+\s*장[\s:.-]*(.*)$', 'chapter', 1),  # Korean chapter

            # Section patterns
            (r'^Section\s+\d+[\.\d]*[\s:.-]*(.*)$', 'section', 2),
            (r'^SECTION\s+\d+[\.\d]*[\s:.-]*(.*)$', 'section', 2),
            (r'^\d+\.\s+(.*)$', 'section', 2),
            (r'^\d+\.\d+\s+(.*)$', 'subsection', 3),

            # Heading patterns (Markdown style)
            (r'^#{1}\s+(.*)$', 'h1', 1),
            (r'^#{2}\s+(.*)$', 'h2', 2),
            (r'^#{3}\s+(.*)$', 'h3', 3),
            (r'^#{4}\s+(.*)$', 'h4', 4),

            # Title patterns (all caps or title case)
            (r'^([A-Z][A-Z\s]{4,})$', 'title', 2),
            (r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,})$', 'title', 2),
        ]

        self.list_patterns = [
            r'^\s*[-*•]\s+',  # Bullet points
            r'^\s*\d+\.\s+',  # Numbered lists
            r'^\s*[a-z]\)\s+',  # Letter lists
            r'^\s*\([a-z]\)\s+',  # Parenthetical lists
        ]

        self.code_block_pattern = r'^```[\s\S]*?```$'
        self.table_pattern = r'^\|.*\|.*\|'

    def extract_structure(self, text: str) -> List[Dict[str, Any]]:
        """Extract document structure from text."""
        structures = []
        lines = text.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check heading patterns
            for pattern, struct_type, level in self.heading_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    title = match.group(1) if match.lastindex else line
                    structures.append({
                        'line_num': i,
                        'type': struct_type,
                        'level': level,
                        'title': title.strip(),
                        'full_text': line
                    })
                    break

        return structures

    def detect_special_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Detect special blocks like code, tables, lists."""
        special_blocks = []
        lines = text.split('\n')

        in_code_block = False
        in_table = False
        in_list = False
        block_start = -1

        for i, line in enumerate(lines):
            # Code blocks
            if '```' in line:
                if not in_code_block:
                    in_code_block = True
                    block_start = i
                else:
                    in_code_block = False
                    special_blocks.append({
                        'type': 'code',
                        'start': block_start,
                        'end': i + 1
                    })

            # Tables
            elif re.match(self.table_pattern, line):
                if not in_table:
                    in_table = True
                    block_start = i
            elif in_table and not re.match(self.table_pattern, line):
                in_table = False
                special_blocks.append({
                    'type': 'table',
                    'start': block_start,
                    'end': i
                })

            # Lists
            list_match = any(re.match(pattern, line) for pattern in self.list_patterns)
            if list_match:
                if not in_list:
                    in_list = True
                    block_start = i
            elif in_list and not list_match and line.strip():
                in_list = False
                special_blocks.append({
                    'type': 'list',
                    'start': block_start,
                    'end': i
                })

        return special_blocks


class SemanticChunker:
    """Main semantic text chunking system."""

    def __init__(self, config: Optional[ChunkConfig] = None):
        """Initialize the chunker with configuration."""
        self.config = config or ChunkConfig()
        self.tokenizer = tiktoken.get_encoding(self.config.encoding_model)
        self.structure_extractor = DocumentStructureExtractor()
        self.chunk_hashes = set()  # For deduplication

        logger.info(f"Initialized SemanticChunker with token range {self.config.min_tokens}-{self.config.max_tokens}")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.tokenizer.encode(text))

    def chunk_text(self, text: str, document_id: Optional[int] = None,
                  page_breaks: Optional[List[int]] = None) -> List[TextChunk]:
        """
        Main chunking method that processes text into semantic chunks.

        Args:
            text: Input text to chunk
            document_id: Optional document ID for reference
            page_breaks: Optional list of character positions where pages break

        Returns:
            List of TextChunk objects
        """
        # Extract document structure
        structures = []
        if self.config.detect_structure:
            structures = self.structure_extractor.extract_structure(text)
            logger.info(f"Extracted {len(structures)} structural elements")

        # Detect special blocks
        special_blocks = self.structure_extractor.detect_special_blocks(text)

        # Create chunks with sliding window
        chunks = self._create_sliding_window_chunks(text, structures, special_blocks, page_breaks)

        # Add hierarchy if needed
        if structures:
            chunks = self._add_chunk_hierarchy(chunks, structures)

        # Deduplicate if enabled
        if self.config.enable_deduplication:
            chunks = self._deduplicate_chunks(chunks)

        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks

    def _create_sliding_window_chunks(self, text: str, structures: List[Dict],
                                     special_blocks: List[Dict],
                                     page_breaks: Optional[List[int]]) -> List[TextChunk]:
        """Create chunks using sliding window approach."""
        chunks = []
        sentences = self._split_into_sentences(text)

        current_chunk = []
        current_tokens = 0
        current_start_char = 0
        chunk_index = 0

        for sent_idx, sentence in enumerate(sentences):
            sent_tokens = self.count_tokens(sentence['text'])

            # Check if adding this sentence exceeds max tokens
            if current_tokens + sent_tokens > self.config.max_tokens and current_chunk:
                # Create chunk
                chunk_text = ' '.join([s['text'] for s in current_chunk])
                chunk = self._create_chunk(
                    chunk_text, chunk_index, current_start_char,
                    current_chunk[-1]['end'], structures, page_breaks
                )
                chunks.append(chunk)
                chunk_index += 1

                # Sliding window overlap
                if self.config.overlap_tokens > 0:
                    # Calculate overlap
                    overlap_chunk = []
                    overlap_tokens = 0

                    for s in reversed(current_chunk):
                        s_tokens = self.count_tokens(s['text'])
                        if overlap_tokens + s_tokens <= self.config.overlap_tokens:
                            overlap_chunk.insert(0, s)
                            overlap_tokens += s_tokens
                        else:
                            break

                    current_chunk = overlap_chunk
                    current_tokens = overlap_tokens
                    if overlap_chunk:
                        current_start_char = overlap_chunk[0]['start']
                else:
                    current_chunk = []
                    current_tokens = 0
                    current_start_char = sentence['start']

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_tokens += sent_tokens

            if not current_chunk:
                current_start_char = sentence['start']

            # Check if we've reached minimum chunk size and there's a good break point
            if (current_tokens >= self.config.min_tokens and
                self._is_good_break_point(sent_idx, sentences, structures)):

                # Check if next section would be too small
                remaining_tokens = sum(
                    self.count_tokens(s['text'])
                    for s in sentences[sent_idx + 1:sent_idx + 5]
                )

                if remaining_tokens < self.config.min_tokens / 2:
                    # Don't break yet, continue adding
                    continue

                # Create chunk at good break point
                chunk_text = ' '.join([s['text'] for s in current_chunk])
                chunk = self._create_chunk(
                    chunk_text, chunk_index, current_start_char,
                    current_chunk[-1]['end'], structures, page_breaks
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap
                if self.config.overlap_tokens > 0 and sent_idx < len(sentences) - 1:
                    overlap_chunk = []
                    overlap_tokens = 0

                    for s in reversed(current_chunk):
                        s_tokens = self.count_tokens(s['text'])
                        if overlap_tokens + s_tokens <= self.config.overlap_tokens:
                            overlap_chunk.insert(0, s)
                            overlap_tokens += s_tokens
                        else:
                            break

                    current_chunk = overlap_chunk
                    current_tokens = overlap_tokens
                    if overlap_chunk:
                        current_start_char = overlap_chunk[0]['start']
                else:
                    current_chunk = []
                    current_tokens = 0
                    if sent_idx < len(sentences) - 1:
                        current_start_char = sentences[sent_idx + 1]['start']

        # Handle remaining text
        if current_chunk:
            chunk_text = ' '.join([s['text'] for s in current_chunk])
            chunk = self._create_chunk(
                chunk_text, chunk_index, current_start_char,
                current_chunk[-1]['end'], structures, page_breaks
            )
            chunks.append(chunk)

        return chunks

    def _split_into_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Split text into sentences with position tracking."""
        # Simple sentence splitting (can be enhanced with spaCy or NLTK)
        sentence_endings = re.compile(r'([.!?])\s+')
        sentences = []

        current_pos = 0
        for match in sentence_endings.finditer(text):
            end_pos = match.end()
            sentence_text = text[current_pos:end_pos].strip()

            if sentence_text:
                sentences.append({
                    'text': sentence_text,
                    'start': current_pos,
                    'end': end_pos
                })
            current_pos = end_pos

        # Add remaining text
        if current_pos < len(text):
            remaining = text[current_pos:].strip()
            if remaining:
                sentences.append({
                    'text': remaining,
                    'start': current_pos,
                    'end': len(text)
                })

        return sentences

    def _is_good_break_point(self, sent_idx: int, sentences: List[Dict],
                            structures: List[Dict]) -> bool:
        """Determine if current position is a good break point."""
        if sent_idx >= len(sentences) - 1:
            return True

        current_sent = sentences[sent_idx]
        next_sent = sentences[sent_idx + 1] if sent_idx < len(sentences) - 1 else None

        # Check for paragraph boundary (double newline)
        if next_sent:
            text_between = current_sent['text']
            if '\n\n' in text_between or text_between.endswith('\n\n'):
                return True

        # Check for section boundary
        for struct in structures:
            if next_sent and abs(struct['line_num'] - sent_idx) <= 1:
                return True

        # Check for list or code block boundaries
        current_text = current_sent['text']
        if any(pattern in current_text for pattern in ['```', '---', '___', '***']):
            return True

        return False

    def _create_chunk(self, text: str, index: int, start_char: int, end_char: int,
                     structures: List[Dict], page_breaks: Optional[List[int]]) -> TextChunk:
        """Create a TextChunk object with metadata."""
        # Find section title
        section_title = None
        for struct in reversed(structures):  # Find most recent section
            struct_pos = struct.get('line_num', 0) * 50  # Approximate position
            if struct_pos <= start_char:
                section_title = struct['title']
                break

        # Determine page numbers
        start_page = None
        end_page = None
        if page_breaks:
            for i, page_break in enumerate(page_breaks):
                if start_char < page_break:
                    start_page = i + 1
                    break
            for i, page_break in enumerate(page_breaks):
                if end_char <= page_break:
                    end_page = i + 1
                    break

        # Create metadata
        metadata = {
            'has_code': '```' in text,
            'has_list': any(re.search(pattern, text, re.MULTILINE)
                          for pattern in self.structure_extractor.list_patterns),
            'has_table': '|' in text and text.count('|') > 2,
            'created_at': datetime.utcnow().isoformat()
        }

        return TextChunk(
            content=text,
            chunk_index=index,
            token_count=self.count_tokens(text),
            start_char=start_char,
            end_char=end_char,
            start_page=start_page,
            end_page=end_page,
            section_title=section_title,
            metadata=metadata
        )

    def _add_chunk_hierarchy(self, chunks: List[TextChunk], structures: List[Dict]) -> List[TextChunk]:
        """Add hierarchical relationships between chunks."""
        # Group chunks by major sections
        section_chunks = {}
        current_section = None

        for chunk in chunks:
            if chunk.section_title:
                current_section = chunk.section_title
                if current_section not in section_chunks:
                    section_chunks[current_section] = []
                section_chunks[current_section].append(chunk)
            elif current_section:
                section_chunks[current_section].append(chunk)

        # Create parent chunks for large sections
        hierarchical_chunks = []
        parent_chunk_id = 0

        for section, section_chunk_list in section_chunks.items():
            if len(section_chunk_list) > 3:  # Create parent chunk for large sections
                # Combine first few chunks as parent
                parent_text = ' '.join([c.content[:500] for c in section_chunk_list[:3]])
                parent_chunk = TextChunk(
                    content=parent_text + '...',
                    chunk_index=parent_chunk_id,
                    token_count=self.count_tokens(parent_text),
                    start_char=section_chunk_list[0].start_char,
                    end_char=section_chunk_list[-1].end_char,
                    section_title=section,
                    chunk_level=0,
                    metadata={'is_parent': True, 'child_count': len(section_chunk_list)}
                )
                hierarchical_chunks.append(parent_chunk)

                # Update children
                for child in section_chunk_list:
                    child.parent_chunk_id = parent_chunk_id
                    child.chunk_level = 1
                    hierarchical_chunks.append(child)

                parent_chunk_id += 1
            else:
                hierarchical_chunks.extend(section_chunk_list)

        # Add chunks without sections
        for chunk in chunks:
            if chunk not in hierarchical_chunks:
                hierarchical_chunks.append(chunk)

        return hierarchical_chunks

    def _deduplicate_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """Remove duplicate chunks based on content hash."""
        unique_chunks = []
        seen_hashes = set()

        for chunk in chunks:
            if chunk.chunk_hash not in seen_hashes:
                unique_chunks.append(chunk)
                seen_hashes.add(chunk.chunk_hash)
            else:
                logger.debug(f"Removed duplicate chunk with hash {chunk.chunk_hash}")

        if len(chunks) != len(unique_chunks):
            logger.info(f"Removed {len(chunks) - len(unique_chunks)} duplicate chunks")

        return unique_chunks

    def merge_small_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """Merge chunks that are too small."""
        merged_chunks = []
        current_merge = None

        for chunk in chunks:
            if chunk.token_count < self.config.min_tokens / 2:
                if current_merge:
                    # Merge with previous
                    current_merge.content += '\n\n' + chunk.content
                    current_merge.token_count += chunk.token_count
                    current_merge.end_char = chunk.end_char
                    current_merge.end_page = chunk.end_page
                else:
                    current_merge = chunk
            else:
                if current_merge:
                    if current_merge.token_count < self.config.min_tokens:
                        # Merge with current
                        chunk.content = current_merge.content + '\n\n' + chunk.content
                        chunk.token_count += current_merge.token_count
                        chunk.start_char = current_merge.start_char
                        chunk.start_page = current_merge.start_page
                        merged_chunks.append(chunk)
                    else:
                        merged_chunks.append(current_merge)
                        merged_chunks.append(chunk)
                    current_merge = None
                else:
                    merged_chunks.append(chunk)

        if current_merge:
            merged_chunks.append(current_merge)

        return merged_chunks