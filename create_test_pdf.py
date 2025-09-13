"""Create a test PDF for pipeline testing."""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY
import datetime

def create_test_pdf(filename="test_document.pdf"):
    """Create a multi-page test PDF with structured content."""

    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
    )

    chapter_style = ParagraphStyle(
        'Chapter',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        alignment=TA_JUSTIFY,
        spaceAfter=12,
    )

    # Title Page
    story.append(Paragraph("TLDRify Test Document", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(PageBreak())

    # Chapter 1
    story.append(Paragraph("Chapter 1: Introduction to Machine Learning", chapter_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("1.1 What is Machine Learning?", section_style))
    story.append(Paragraph(
        """Machine learning is a subset of artificial intelligence (AI) that provides systems the ability to
        automatically learn and improve from experience without being explicitly programmed. Machine learning
        focuses on the development of computer programs that can access data and use it to learn for themselves.
        The process of learning begins with observations or data, such as examples, direct experience, or
        instruction, in order to look for patterns in data and make better decisions in the future based on
        the examples that we provide.""",
        body_style
    ))

    story.append(Paragraph("1.2 Types of Machine Learning", section_style))
    story.append(Paragraph(
        """There are several types of machine learning algorithms. Supervised learning algorithms build a
        mathematical model of a set of data that contains both the inputs and the desired outputs. The data
        is known as training data, and consists of a set of training examples. Each training example has one
        or more inputs and the desired output, also known as a supervisory signal.""",
        body_style
    ))

    story.append(Paragraph(
        """Unsupervised learning algorithms take a set of data that contains only inputs, and find structure
        in the data, like grouping or clustering of data points. The algorithms therefore learn from test data
        that has not been labeled, classified or categorized. Instead of responding to feedback, unsupervised
        learning algorithms identify commonalities in the data and react based on the presence or absence of
        such commonalities in each new piece of data.""",
        body_style
    ))

    story.append(PageBreak())

    # Chapter 2
    story.append(Paragraph("Chapter 2: Deep Learning Fundamentals", chapter_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("2.1 Neural Networks", section_style))
    story.append(Paragraph(
        """Artificial neural networks (ANNs), usually simply called neural networks (NNs), are computing
        systems vaguely inspired by the biological neural networks that constitute animal brains. An ANN is
        based on a collection of connected units or nodes called artificial neurons, which loosely model the
        neurons in a biological brain. Each connection, like the synapses in a biological brain, can transmit
        a signal to other neurons.""",
        body_style
    ))

    story.append(Paragraph("2.2 Convolutional Neural Networks", section_style))
    story.append(Paragraph(
        """A convolutional neural network (CNN, or ConvNet) is a class of deep neural networks, most commonly
        applied to analyzing visual imagery. They are also known as shift invariant or space invariant artificial
        neural networks (SIANN), based on their shared-weights architecture and translation invariance
        characteristics. They have applications in image and video recognition, recommender systems, image
        classification, medical image analysis, natural language processing, and financial time series.""",
        body_style
    ))

    story.append(Paragraph(
        """CNNs are regularized versions of multilayer perceptrons. Multilayer perceptrons usually mean fully
        connected networks, that is, each neuron in one layer is connected to all neurons in the next layer.
        The "fully-connectedness" of these networks makes them prone to overfitting data. Typical ways of
        regularization include adding some form of magnitude measurement of weights to the loss function.""",
        body_style
    ))

    story.append(PageBreak())

    # Chapter 3
    story.append(Paragraph("Chapter 3: Natural Language Processing", chapter_style))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("3.1 Introduction to NLP", section_style))
    story.append(Paragraph(
        """Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial
        intelligence concerned with the interactions between computers and human language, in particular how
        to program computers to process and analyze large amounts of natural language data. The goal is a
        computer capable of understanding the contents of documents, including the contextual nuances of the
        language within them.""",
        body_style
    ))

    story.append(Paragraph("3.2 Transformers and Attention Mechanisms", section_style))
    story.append(Paragraph(
        """The Transformer is a deep learning model introduced in 2017, used primarily in the field of natural
        language processing (NLP). Like recurrent neural networks (RNNs), Transformers are designed to handle
        sequential input data, such as natural language, for tasks such as translation and text summarization.
        However, unlike RNNs, Transformers do not require that the sequential data be processed in order. Due
        to this feature, the Transformer allows for much more parallelization than RNNs during training.""",
        body_style
    ))

    story.append(Paragraph(
        """Since their introduction, Transformers have become the model of choice for NLP problems, replacing
        older recurrent neural network models such as the long short-term memory (LSTM). The additional training
        parallelization allows training on larger datasets than was once possible. This led to the development
        of pretrained systems such as BERT and GPT, which were trained with large language datasets, such as
        the Wikipedia Corpus and Common Crawl, and can be fine-tuned for specific tasks.""",
        body_style
    ))

    # Build PDF
    doc.build(story)
    print(f"✅ Created test PDF: {filename}")
    return filename

if __name__ == "__main__":
    create_test_pdf()
