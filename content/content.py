import sys
import random
import urllib
import logging
import PIL.Image, PIL.ImageTk, cStringIO
import Tkinter

# Mother class for content categories
class Content:
    all_categories = {}
    all_content = []

    def __init__(self, str_, categories = [], score = 1):
        self.widget_ = None
        self.str_ = str_
        self.categories = categories
        for category in categories:
            # Populate the categories dictionnary
            if not category in Content.all_categories.keys():
                # Init the score at 1
                Content.all_categories[category] = 1
        self.score = score

    def __str__(self):
        return self.str_

    # Return the content's score
    def get_score(self):
        # To avoid repeating the same content, ignore individual score
        #total_score = self.score
        total_score = 0
        for category in self.categories:
            total_score += Content.all_categories[category]
        return total_score

    # Alter the score
    def boost(self, boost_value):
        for category in self.categories:
            Content.all_categories[category] *= boost_value
        self.score *= boost_value * boost_value
    
    def show(self, gui=None):
        # This should be called
        raise NotImplementedError

    def hide(self, gui=None):
        if gui and self.widget_:
            # Clear the widget
            self.widget_.pack_forget()

    # Sample one content, weighted with the scores by default
    @classmethod
    def get_content(self, weighted=True):
        total = sum(c.get_score() for c in self.all_content)
        prob = random.uniform(0, total)
        upto = 0
        for content in self.all_content:
            if weighted:
                score = content.get_score()
            else:
                score = 1
            if upto + score >= prob:
                return content
            upto += score

    # Resize images for GUI visualization
    # TODO : adjust to GUI's size
    @staticmethod
    def resize(img):
        basewidth = 780
        baseheight = 500
        if img.size[0] > basewidth:
            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            if hsize > baseheight:
                wpercent = (baseheight / float(img.size[1]))
                wsize = int((float(img.size[0]) * float(wpercent)))
                return img.resize((wsize, baseheight), PIL.Image.ANTIALIAS)
            return img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
        else:
            return img
    
# Subclass for local images
class Image(Content):
    def __init__(self, str_, images, categories = [], score = 1):
        Content.__init__(self, str_, categories, score)
        self.images = images
        self.widget_ = None

    def show(self, gui=None):
        img = Content.resize(PIL.Image.open(random.sample(self.images, 1)[0]))
        if gui:
            # Show with a Tkinter widget
            photo = PIL.ImageTk.PhotoImage(img)
            self.widget_ = Tkinter.Text(gui, relief="flat", background=gui.cget("background"), borderwidth=0)
            self.widget_.insert(Tkinter.INSERT, '\n')
            self.widget_.image_create(Tkinter.INSERT, image=photo)
            self.widget_.image = photo
            self.widget_.config(state=Tkinter.DISABLED)
            self.widget_.pack(fill=Tkinter.BOTH,expand=True)
        else:
            # Use PIL to display the image
            img.show()

# Subclass for images on the web
class WebImage(Content):
    def __init__(self, str_, urls, categories = [], score = 1):
        Content.__init__(self, str_, categories, score)
        self.urls = urls

    def show(self, gui=None):
        try:
            # Try to get the image from the web
            f = cStringIO.StringIO(urllib.urlopen(random.sample(self.urls, 1)[0]).read())
            img = Content.resize(PIL.Image.open(f))
            if gui:
                # Show with a Tkinter widget
                photo = PIL.ImageTk.PhotoImage(img)
                self.widget_ = Tkinter.Text(gui, relief="flat", background=gui.cget("background"), borderwidth=0)
                self.widget_.insert(Tkinter.INSERT, '\n')
                self.widget_.image_create(Tkinter.INSERT, image=photo)
                self.widget_.image = photo
                self.widget_.config(state=Tkinter.DISABLED)
                self.widget_.pack(fill=Tkinter.BOTH,expand=True)
            else:
                # Use PIL to display the image
                img.show()
        except Exception as e:
            logging.warn("Cannot download image" + str(e))
            raise

class GifLabel(Tkinter.Label):
    def __init__(self, master, im):
        seq = []
        try:
            while 1:
                seq.append(im.copy())
                im.seek(len(seq))
        except EOFError:
                pass

        try:
            self.delay = max(im.info['duration'], 50)
            self.delay = min(200, self.delay)
        except KeyError:
            self.delay = 50

        first = seq[0].convert('RGBA')
        self.frames = [PIL.ImageTk.PhotoImage(first)]

        Tkinter.Label.__init__(self, master, image=self.frames[0])

        temp = seq[0]
        for image in seq[1:]:
            temp.paste(image)
            frame = temp.convert('RGBA')
            self.frames.append(PIL.ImageTk.PhotoImage(frame))
        self.idx = 0
        self.cancel = self.after(self.delay, self.play)

    def play(self):
        self.config(image=self.frames[self.idx])
        self.idx += 1
        if self.idx == len(self.frames):
            self.idx = 0
        self.cancel = self.after(self.delay, self.play)


class WebGif(Content):
    def __init__(self, str_, urls, categories = [], score = 1):
        Content.__init__(self, str_, categories, score)
        self.urls = urls

    def show(self, gui=None):
        try:
            # Try to get the gif from the web
            f = cStringIO.StringIO(urllib.urlopen(random.sample(self.urls, 1)[0]).read())
            img = Content.resize(PIL.Image.open(f))
            if gui:
                self.widget_ = GifLabel(gui, img)
                self.widget_.pack(fill=Tkinter.BOTH,expand=True)
            else:
                raise NotImplementedError
        except Exception as e:
            logging.warn("Cannot display gif image " + str(e))
            raise
    
# Subclass for local text
class Text(Content):
    def __init__(self, str_, texts, categories = [], score = 1):
        Content.__init__(self, str_, categories, score)
        self.texts = texts

    def show(self, gui=None):
        text = str(self) +  ":\n" + random.sample(self.texts, 1)[0]
        if gui:
            # Show with Tkinter
            self.widget_ = Tkinter.Text(gui, relief="flat", background=gui.cget("background"), borderwidth=0)
            self.widget_.insert(Tkinter.INSERT, text)
            self.widget_.config(state=Tkinter.DISABLED)
            self.widget_.pack(fill=Tkinter.BOTH,expand=True)
        else:
            # Print in the console
            print text

# URLS
calvin_and_hobbes = [
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880601.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880602.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880603.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880604.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880605.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880606.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880607.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880608.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880609.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880610.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880611.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880612.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880613.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880614.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880615.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880616.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880617.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880618.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880619.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880620.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880621.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880622.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880623.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880624.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880625.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880626.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880627.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880628.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880629.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1988/06/19880630.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950801.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950802.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950803.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950804.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950805.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950806.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950807.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950808.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950809.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950810.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950811.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950812.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950813.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950814.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950815.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950816.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950817.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950818.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950819.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950820.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950821.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950822.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950823.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950824.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950825.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950826.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950827.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950828.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950829.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950830.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/08/19950831.gif",
        ]


cyanide_and_happiness = [
        "http://files.explosm.net/comics/Rob/santalist.png",
        "http://files.explosm.net/comics/Matt/bad-choice-of-words.png",
        "http://files.explosm.net/comics/Kris/wake.png",
        "http://files.explosm.net/comics/Dave/dammitjohnsondammit.png",
        "http://files.explosm.net/comics/Rob/mydad.png",
        "http://files.explosm.net/comics/guest4/AdgeRiano.jpg",
        "http://files.explosm.net/comics/Matt/is-it-white-riot.jpg",
        "http://files.explosm.net/comics/Dave/seeicouldvebeenawaybetterjesusidhaveusedthatcrownofthornsasmythinkingcap.png",
        "http://files.explosm.net/comics/Rob/COOLSHADES2.png",
        "http://files.explosm.net/comics/Dave/comicsasquatch1.png",
        "http://files.explosm.net/comics/Dave/comiceviltwin1.png",
        "http://files.explosm.net/comics/Dave/comicgoldfisharmy1.png",
        "http://files.explosm.net/comics/Rob/charles_tree.png",
        "http://files.explosm.net/comics/Kris/holy.png",
        "http://files.explosm.net/comics/Kris/pills.png",
        "http://files.explosm.net/comics/Rob/finished.png",
        "http://files.explosm.net/comics/Rob/weird.png",
        "http://files.explosm.net/comics/Dave/comicadoptionabortion1.png",
        "http://files.explosm.net/comics/Matt/Timmy-got-a-bike-for-Xmas.png",
        "http://files.explosm.net/comics/carcrash.jpg",
        "http://files.explosm.net/comics/Rob/littleguys.png",
        "http://files.explosm.net/comics/Kris/homosexuals.png",
        "http://files.explosm.net/comics/Dave/comicnoskin1.png",
        "http://files.explosm.net/comics/Kris/babysitting0001.jpg",
        "http://files.explosm.net/comics/Rob/aids.jpg",
        "http://files.explosm.net/comics/lastmeal.png",
        "http://files.explosm.net/comics/Rob/charles_poster2.png",
        "http://files.explosm.net/comics/Rob/porn-everywhere3.png",
        "http://files.explosm.net/comics/Rob/happy-birthday-dave.png",
        "http://files.explosm.net/comics/guest6/CRW_jonah_v_essay.png",
        "http://files.explosm.net/files/Ryan-Hudson-Guest.png",
        "http://files.explosm.net/comics/Dave/comicoptimisticmannew.png",
        "http://files.explosm.net/comics/Dave/hitthesack.png",
        "http://files.explosm.net/comics/Kris/order.png",
        "http://files.explosm.net/comics/Rob/airport-security.png",
        "http://files.explosm.net/comics/Kris/snail.png",
        "http://files.explosm.net/comics/Kris/cake.png",
        "http://files.explosm.net/comics/Rob/ramblingman.png",
        "http://files.explosm.net/comics/Dave/comictruestorynew.png",
        "http://files.explosm.net/comics/Dave/comiccomediannnnn.png",
        "http://files.explosm.net/comics/Rob/dogname.png",
        "http://files.explosm.net/comics/Matt/Dick-move,-trail-mix-company.-Dick-move..png",
        "http://files.explosm.net/comics/Kris/seuss.png",
        "http://files.explosm.net/comics/Dave/harassmentoldboy.png",
        "http://files.explosm.net/comics/Rob/howifeel.png",
        "http://files.explosm.net/comics/Rob/heya.png",
        "http://files.explosm.net/comics/Kris/toilet.png",
        "http://files.explosm.net/comics/Kris/crying.png",
    ]


xkcd = [
        "http://imgs.xkcd.com/comics/2009_called.png",
        "http://imgs.xkcd.com/comics/alternate_universe.png",
        "http://imgs.xkcd.com/comics/a-minus-minus.png",
        "http://imgs.xkcd.com/comics/applied_math.png",
        "http://imgs.xkcd.com/comics/arrow.png",
        "http://imgs.xkcd.com/comics/aspect_ratio.png",
        "http://imgs.xkcd.com/comics/authorization.png",
        "http://imgs.xkcd.com/comics/automation.png",
        "http://imgs.xkcd.com/comics/centrifugal_force.png",
        "http://imgs.xkcd.com/comics/cirith_ungol.png",
        "http://imgs.xkcd.com/comics/crime_scene.png",
        "http://imgs.xkcd.com/comics/dental_nerve.png",
        "http://imgs.xkcd.com/comics/drinking_fountains.png",
        "http://imgs.xkcd.com/comics/est.png",
        "http://imgs.xkcd.com/comics/every_damn_morning.png",
        "http://imgs.xkcd.com/comics/exoplanet_names.png",
        "http://imgs.xkcd.com/comics/finish_line.png",
        "http://imgs.xkcd.com/comics/first.png",
        "http://imgs.xkcd.com/comics/fortune_cookies.png",
        "http://imgs.xkcd.com/comics/gravitational_mass.jpg",
        "http://imgs.xkcd.com/comics/jacket.jpg",
        "http://imgs.xkcd.com/comics/joshing.png",
        "http://imgs.xkcd.com/comics/krypton.png",
        "http://imgs.xkcd.com/comics/latitude.png",
        "http://imgs.xkcd.com/comics/light.jpg",
        "http://imgs.xkcd.com/comics/love.jpg",
        "http://imgs.xkcd.com/comics/malamanteau.png",
        "http://imgs.xkcd.com/comics/malaria.jpg",
        "http://imgs.xkcd.com/comics/mc_hammer_slide.png",
        "http://imgs.xkcd.com/comics/microdrones.png",
        "http://imgs.xkcd.com/comics/mission_to_culture.png",
        "http://imgs.xkcd.com/comics/move_fast_and_break_things.png",
        "http://imgs.xkcd.com/comics/nerd_sniping.png",
        "http://imgs.xkcd.com/comics/other_car.jpg",
        "http://imgs.xkcd.com/comics/pastime.png",
        "http://imgs.xkcd.com/comics/photoshops.png",
        "http://imgs.xkcd.com/comics/proof.png",
        "http://imgs.xkcd.com/comics/reset.png",
        "http://imgs.xkcd.com/comics/screenshot.png",
        "http://imgs.xkcd.com/comics/scribblenauts.png",
        "http://imgs.xkcd.com/comics/semicontrolled_demolition.png",
        "http://imgs.xkcd.com/comics/six_months.png",
        "http://imgs.xkcd.com/comics/star_trek_into_darkness.png",
        "http://imgs.xkcd.com/comics/success.png",
        "http://imgs.xkcd.com/comics/tap_that_ass.png",
        "http://imgs.xkcd.com/comics/tech_support_cheat_sheet.png",
        "http://imgs.xkcd.com/comics/two_years.png",
        "http://imgs.xkcd.com/comics/voting_machines.png"
]

kitten = ["http://www.randomkittengenerator.com/cats/rotator.php"]

animal_gifs = [
    "http://i.imgur.com/ad4YO3P.gif",
    "http://i.imgur.com/Hc0EXFR.gif",
    "http://i.imgur.com/AIfyQ8d.gif",
    "http://i.imgur.com/GdLzOKc.gif",
    "http://i.imgur.com/9w2FM0n.gif",
    "http://i.imgur.com/3VRU6af.gif",
    "http://i.imgur.com/E172dSs.gif",
    "http://i.imgur.com/qjWUaCM.gif",
    "http://i.imgur.com/DX33frn.gif",
    "http://i.imgur.com/nXpWsOj.gif",
    "http://i.imgur.com/TJZyaVy.gif",
    "http://i.imgur.com/BaUl5RN.gif",
    "http://i.imgur.com/BQLLu3G.gif",
    "http://i.imgur.com/XDGIdT8.gif",
    "http://i.imgur.com/sblZK5j.gif",
    "http://i.imgur.com/f7QJFxd.gif",
    "http://i.imgur.com/GbU1Vai.gif",
    "http://i.imgur.com/6esSdOr.gif",
    "http://i.imgur.com/2W26LGH.gif",
    "http://i.imgur.com/ng16KuG.gif",
    "http://i.imgur.com/1D5sb6a.gif",
    "http://i.imgur.com/pJ0ptxG.gif",
    "http://i.imgur.com/sHU443Q.gif",
    "http://i.imgur.com/VXPv9lN.gif",
    "http://i.imgur.com/cPkI2Fi.gif",
    "http://i.imgur.com/1FurBDb.gif",
    "http://i.imgur.com/W5d1a9D.gif",
    "http://i.imgur.com/1F1cn5Z.gif",
    "http://i.imgur.com/OvTS5rH.gif",
    "http://i.imgur.com/IUmRyN0.gif",
    "http://i.imgur.com/sfhIBFP.gif",
    "http://i.imgur.com/RMmlfJ5.gif",
    "http://i.imgur.com/quqNDor.gif",
    "http://i.imgur.com/mqOmfP1.gif",
    "http://i.imgur.com/ad4YO3P.gif",
    "http://i.imgur.com/Hc0EXFR.gif",
    "http://i.imgur.com/AIfyQ8d.gif",
    "http://i.imgur.com/GdLzOKc.gif",
    "http://i.imgur.com/9w2FM0n.gif",
    "http://i.imgur.com/3VRU6af.gif",
    "http://i.imgur.com/E172dSs.gif",
    "http://i.imgur.com/qjWUaCM.gif",
    "http://i.imgur.com/DX33frn.gif",
    "http://i.imgur.com/nXpWsOj.gif",
    "http://i.imgur.com/TJZyaVy.gif",
    "http://i.imgur.com/BaUl5RN.gif",
    "http://i.imgur.com/BQLLu3G.gif",
    "http://i.imgur.com/XDGIdT8.gif",
    "http://i.imgur.com/sblZK5j.gif",
    "http://i.imgur.com/f7QJFxd.gif",
    "http://i.imgur.com/GbU1Vai.gif",
    "http://i.imgur.com/GbU1Vai.gif",
    "http://i.imgur.com/f7QJFxd.gif",
    "http://i.imgur.com/ad4YO3P.gif",
    "http://i.imgur.com/Hc0EXFR.gif",
    "http://i.imgur.com/d30QNTi.gif",
    "http://i.imgur.com/2hZGdnU.gif",
    "http://i.imgur.com/d30QNTi.gif",
    "http://i.imgur.com/g5ItBAF.gif",
    "http://i.imgur.com/cpfSmCQ.gif",
    "http://i.imgur.com/PAVgB2s.gif",
    "http://i.imgur.com/aWpq3Wf.gif",
    "http://i.imgur.com/Jx4Pcvy.gif",
    "http://i.imgur.com/yEKynhv.gif",
    "http://i.imgur.com/PxQy3ZN.gif",
    "http://i.imgur.com/wLKSsaT.gif",
    "http://i.imgur.com/2ldG275.gif",
    "http://i.imgur.com/SB3KTgG.gif",
    "http://i.imgur.com/Ien5k2a.gif",
    "http://i.imgur.com/lpqN31u.gif",
    "http://i.imgur.com/I0aE8jd.gif",
    "http://i.imgur.com/hSFGAQH.gif",
    "http://i.imgur.com/DyikqOx.gif",
    "http://i.imgur.com/dm3k0Nd.gif",
    "http://i.imgur.com/EXZ2sbS.gif",
    "http://i.imgur.com/fPassLy.gif",
    "http://i.imgur.com/SJF1YSy.gif",
    "http://i.imgur.com/C5ivpYq.gif",
    "http://i.imgur.com/vS67FqB.gif",
    "http://i.imgur.com/2P5OjL5.gif",
    "http://i.imgur.com/mrtywgX.gif"
]
