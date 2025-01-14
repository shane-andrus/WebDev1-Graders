from setuptools import setup, find_packages

setup(
    name='grading_automation_tool',
    version='1.0.0',
    author='Shane Andrus',
    author_email='shane.andrus@ccsdut.org',
    description='A tool for grading HTML assignments and automating grading in Canvas.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/shane-andrus/WebDev1-Graders',
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4',
        'pandas',
        'selenium',
        'pygetwindow',
        'requests',
        'urllib3'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'grade-heading=heading_hr_grader:main',
            'grade-myfirst=my_first_webpage_grader:main',
            'grade-mysecond=my_second_webpage_grader:main',
        ],
    },
    include_package_data=True,
)
