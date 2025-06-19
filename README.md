# ParticleText

In this repository, I tried something called creative coding in Python and panda3d. To create an animation in which text is broken up into particles and flies away, I first created easing functions( [pytweener](https://github.com/taKana671/pytweener)). The text is represented using panda3D's GeomPoints. I dynamically create a text image (Numpy.ndarray in python), and from that image, determine the position of the points to form the text. The position of the flying particles is calculated using PerlinNoise, SimplexNoise([NoiseTexture](https://github.com/taKana671/NoiseTexture)), and random numbers.

The animation can be seen by running `particle_text.py`. It is played back continuously, with the positions of particles flying calculated by different methods, such as PerlinNoise, SimplexNoise, FractalPerlinNoise, random numbers, delayed start, and so on.

https://github.com/user-attachments/assets/3396a11e-0414-4a2f-a9c8-9200629cf4cc



Running `easing_function_demo.py` shows how the particles' movements are changed by the easing functions.

https://github.com/user-attachments/assets/b1b60867-a955-4ebe-b0fd-af1b67f9a6ae

# Requirements

* Panda3D 1.10.15
* numpy 2.2.4
* pillow 11.1.0
* Cython 3.0.12
* opencv-contrib-python 4.11.0.86
* opencv-python 4.11.0.86

# Environment

* Python 3.12
* Windows11


# Usage

### Clone this repository with submodule.

```
git clone --recursive https://github.com/taKana671/ParticleText.git
```

### Build cython code.

```
cd ParticleText
python setup.py build_ext --inplace
```

If the error like "ModuleNotFoundError: No module named ‘distutils’" occurs, install the setuptools.

```
pip install setuptools
```

### running particle_text.py

```
cd ParticleText
python particle_text.py
```

### running easing_function_demo.py

Select the function type using the radio buttons in the first column from the left, and then select in, out, or in_out using the radio buttons in the second column from the left.

```
cd ParticleText
python easing_function_demo.py
```


