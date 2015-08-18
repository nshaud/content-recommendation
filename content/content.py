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
        if weighted:
            total = sum(c.get_score() for c in self.all_content)
        else:
            total = len(self.all_content)
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
            url = random.sample(self.urls, 1)[0]
            # Try to get the image from the web
            f = cStringIO.StringIO(urllib.urlopen(url).read())
            img = Content.resize(PIL.Image.open(f))
            logging.info("URL : " + url)
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
        gif_palette = im.getpalette()
        try:
            while 1:
                im.putpalette(gif_palette)
                seq.append(im.copy())
                im.seek(len(seq))
        except EOFError:
                pass

        try:
            self.delay = im.info['duration']
            if self.delay == 0:
                self.delay = 50
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
            url = random.sample(self.urls, 1)[0]
            logging.info("URL : " + url)
            f = cStringIO.StringIO(urllib.urlopen(url).read())
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
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950401.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950402.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950402.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950402.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950403.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950404.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950405.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950406.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950407.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950408.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950411.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950410.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950412.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1995/04/19950415.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870702.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870701.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870703.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870704.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870706.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870707.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870708.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870709.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870711.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870713.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870714.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870713.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1987/07/19870721.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1989/03/19890302.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1989/03/19890303.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1989/03/19890304.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1992/06/19920608.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1992/06/19920612.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1992/06/19920615.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1992/06/19920616.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1992/06/19920622.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1992/06/19920623.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940101.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940103.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940104.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940105.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940106.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940108.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940120.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940121.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940122.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940125.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940127.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940128.gif",
        "http://marcel-oehler.marcellosendos.ch/comics/ch/1994/01/19940131.gif"
        ]


cyanide_and_happiness = [
        "http://files.explosm.net/comics/Matt/return-of-the-squeeze.jpg",
        "http://files.explosm.net/comics/Kris/cool.png",
        "http://files.explosm.net/comics/Dave/comicresolution1.png",
        "http://files.explosm.net/comics/Kris/pants0001.jpg",
        "http://files.explosm.net/comics/Rob/superjerk.jpg",
        "http://files.explosm.net/comics/Rob/problems.gif",
        "http://files.explosm.net/comics/Kris/paranoid.png",
        "http://files.explosm.net/comics/spider.gif",
        "http://files.explosm.net/comics/Rob/goatee.png",
        "http://files.explosm.net/comics/Kris/hooked.png",
        "http://files.explosm.net/comics/Dave/comicarcheryamusing.png",
        "http://files.explosm.net/comics/Dave/comicopticiansnew.png",
        "http://files.explosm.net/comics/Kris/machine.png",
        "http://files.explosm.net/comics/Rob/resume.png",
        "http://files.explosm.net/comics/Kris/Bargain.png",
        "http://files.explosm.net/comics/Kris/bully2.png",
        "http://files.explosm.net/comics/Dave/comicpursestolennew.png",
        "http://files.explosm.net/comics/Matt/Totally-not-an-excuse-to-copy-paste-all-the-characters.png",
        "http://files.explosm.net/comics/Rob/santalist.png",
        "http://files.explosm.net/comics/Matt/bad-choice-of-words.png",
        "http://files.explosm.net/comics/Kris/wake.png",
        "http://files.explosm.net/comics/Dave/dammitjohnsondammit.png",
        "http://files.explosm.net/comics/Rob/mydad.png",
        "http://files.explosm.net/comics/Matt/is-it-white-riot.jpg",
        "http://files.explosm.net/comics/Rob/COOLSHADES2.png",
        "http://files.explosm.net/comics/Dave/comicsasquatch1.png",
        "http://files.explosm.net/comics/Dave/comiceviltwin1.png",
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
        "http://files.explosm.net/comics/Dave/hitthesack.png",
        "http://files.explosm.net/comics/Kris/order.png",
        "http://files.explosm.net/comics/Rob/airport-security.png",
        "http://files.explosm.net/comics/Kris/snail.png",
        "http://files.explosm.net/comics/Kris/cake.png",
        "http://files.explosm.net/comics/Rob/ramblingman.png",
        "http://files.explosm.net/comics/Dave/comiccomediannnnn.png",
        "http://files.explosm.net/comics/Rob/dogname.png",
        "http://files.explosm.net/comics/Kris/seuss.png",
        "http://files.explosm.net/comics/Dave/harassmentoldboy.png",
        "http://files.explosm.net/comics/Rob/howifeel.png",
        "http://files.explosm.net/comics/Rob/heya.png",
        "http://files.explosm.net/comics/Kris/toilet.png",
        "http://files.explosm.net/comics/Kris/crying.png",
    ]


xkcd = [
        "http://imgs.xkcd.com/comics/terminology.png",
        "http://imgs.xkcd.com/comics/explorers.png",
        "http://imgs.xkcd.com/comics/porn_folder.png",
        "http://imgs.xkcd.com/comics/spice_girl.png",
        "http://imgs.xkcd.com/comics/golden_hammer.png",
        "http://imgs.xkcd.com/comics/pi_vs_tau.png",
        "http://imgs.xkcd.com/comics/tones.png",
        "http://imgs.xkcd.com/comics/time_machines.png",
        "http://imgs.xkcd.com/comics/psychic.png",
        "http://imgs.xkcd.com/comics/when_you_assume.png",
        "http://imgs.xkcd.com/comics/star_wars.png",
        "http://imgs.xkcd.com/comics/yogurt.png",
        "http://imgs.xkcd.com/comics/workflow.png",
        "http://imgs.xkcd.com/comics/moon_landing.png",
        "http://imgs.xkcd.com/comics/answers.png",
        "http://imgs.xkcd.com/comics/six_words.png",
        "http://imgs.xkcd.com/comics/giraffes.png",
        "http://imgs.xkcd.com/comics/lincoln_douglas.png",
        "http://imgs.xkcd.com/comics/too_old_for_this_shit.png",
        "http://imgs.xkcd.com/comics/fourier.jpg",
        "http://imgs.xkcd.com/comics/mystery_news.png",
        "http://imgs.xkcd.com/comics/slippery_slope.png",
        "http://imgs.xkcd.com/comics/simultaneous.png",
        "http://imgs.xkcd.com/comics/horse.png",
        "http://imgs.xkcd.com/comics/typical_morning_routine.png",
        "http://imgs.xkcd.com/comics/scantron.png",
        "http://imgs.xkcd.com/comics/sports_cheat_sheet.png",
        "http://imgs.xkcd.com/comics/troubleshooting.png",
        "http://imgs.xkcd.com/comics/self_description.png",
        "http://imgs.xkcd.com/comics/going_west.png",
        "http://imgs.xkcd.com/comics/unique_date.png",
        "http://imgs.xkcd.com/comics/natural_parenting.png",
        "http://imgs.xkcd.com/comics/puzzle.png",
        "http://imgs.xkcd.com/comics/not_enough_work.png",
        "http://imgs.xkcd.com/comics/myspace.png",
        "http://imgs.xkcd.com/comics/pain_rating.png",
        "http://imgs.xkcd.com/comics/git_commit.png",
        "http://imgs.xkcd.com/comics/extended_mind.png",
        "http://imgs.xkcd.com/comics/date.png",
        "http://imgs.xkcd.com/comics/travelling_salesman_problem.png",
        "http://imgs.xkcd.com/comics/the_sake_of_argument.png",
        "http://imgs.xkcd.com/comics/sword_in_the_stone.png",
        "http://imgs.xkcd.com/comics/convincing_pickup_line.png",
        "http://imgs.xkcd.com/comics/laptop_hell.png",
        "http://imgs.xkcd.com/comics/hard_reboot.png",
        "http://imgs.xkcd.com/comics/sticks_and_stones.png",
        "http://imgs.xkcd.com/comics/commitment.png",
        "http://imgs.xkcd.com/comics/compass_and_straightedge.png",
        "http://imgs.xkcd.com/comics/2009_called.png",
        "http://imgs.xkcd.com/comics/westleys_a_dick.png",
        "http://imgs.xkcd.com/comics/geography.png",
        "http://imgs.xkcd.com/comics/milk.png",
        "http://imgs.xkcd.com/comics/server_attention_span.png",
        "http://imgs.xkcd.com/comics/rba.png",
        "http://imgs.xkcd.com/comics/the_drake_equation.png"
]

kitten = ["http://www.randomkittengenerator.com/cats/rotator.php"]

animal_gifs = [
    "http://i.imgur.com/1D5sb6a.gif",
    "http://i.imgur.com/1F1cn5Z.gif",
    "http://i.imgur.com/1FurBDb.gif",
    "http://i.imgur.com/2ldG275.gif",
    "http://i.imgur.com/2P5OjL5.gif",
    "http://i.imgur.com/2W26LGH.gif",
    "http://i.imgur.com/3VRU6af.gif",
    "http://i.imgur.com/6esSdOr.gif",
    "http://i.imgur.com/9w2FM0n.gif",
    "http://i.imgur.com/ad4YO3P.gif",
    "http://i.imgur.com/AIfyQ8d.gif",
    "http://i.imgur.com/aWpq3Wf.gif",
    "http://i.imgur.com/BaUl5RN.gif",
    "http://i.imgur.com/BQLLu3G.gif",
    "http://i.imgur.com/C5ivpYq.gif",
    "http://i.imgur.com/cpfSmCQ.gif",
    "http://i.imgur.com/cPkI2Fi.gif",
    "http://i.imgur.com/d30QNTi.gif",
    "http://i.imgur.com/dm3k0Nd.gif",
    "http://i.imgur.com/DX33frn.gif",
    "http://i.imgur.com/DyikqOx.gif",
    "http://i.imgur.com/E172dSs.gif",
    "http://i.imgur.com/EXZ2sbS.gif",
    "http://i.imgur.com/f7QJFxd.gif",
    "http://i.imgur.com/fPassLy.gif",
    "http://i.imgur.com/g5ItBAF.gif",
    "http://i.imgur.com/GbU1Vai.gif",
    "http://i.imgur.com/GdLzOKc.gif",
    "http://i.imgur.com/Hc0EXFR.gif",
    "http://i.imgur.com/hSFGAQH.gif",
    "http://i.imgur.com/I0aE8jd.gif",
    "http://i.imgur.com/IUmRyN0.gif",
    "http://i.imgur.com/Jx4Pcvy.gif",
    "http://i.imgur.com/lpqN31u.gif",
    "http://i.imgur.com/mqOmfP1.gif",
    "http://i.imgur.com/mrtywgX.gif"
    "http://i.imgur.com/ng16KuG.gif",
    "http://i.imgur.com/OvTS5rH.gif",
    "http://i.imgur.com/PAVgB2s.gif",
    "http://i.imgur.com/pJ0ptxG.gif",
    "http://i.imgur.com/PxQy3ZN.gif",
    "http://i.imgur.com/qjWUaCM.gif",
    "http://i.imgur.com/quqNDor.gif",
    "http://i.imgur.com/RMmlfJ5.gif",
    "http://i.imgur.com/SB3KTgG.gif",
    "http://i.imgur.com/sblZK5j.gif",
    "http://i.imgur.com/sfhIBFP.gif",
    "http://i.imgur.com/sHU443Q.gif",
    "http://i.imgur.com/SJF1YSy.gif",
    "http://i.imgur.com/TJZyaVy.gif",
    "http://i.imgur.com/vS67FqB.gif",
    "http://i.imgur.com/VXPv9lN.gif",
    "http://i.imgur.com/W5d1a9D.gif",
    "http://i.imgur.com/wLKSsaT.gif",
    "http://i.imgur.com/XDGIdT8.gif",
    "http://i.imgur.com/yEKynhv.gif"
]
