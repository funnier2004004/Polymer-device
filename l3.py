"""Prescribed zero-mean L3 inverse; Practical Methods Guide pp. 10-12."""
import numpy as np

SEED = 60280503
NOISE_DRAWS = 500
COORD = np.linspace(-2.7, 2.7, 10)
MULTIPLIERS = (.01,.1,1.,10.,100.)


def validate(A, repeats):
    if A.shape != (128,100) or repeats.shape != (3,128):
        raise ValueError('L3 requires A=(128,100) and repeats=(3,128)')
    if not np.isfinite(A).all() or not np.isfinite(repeats).all():
        raise ValueError('Non-finite L3 input')
    if np.max(abs(A.sum(axis=1))) >= 1e-11:
        raise ValueError('A does not annihilate the constant map')


def gradient_matrix():
    rows=[]
    for i in range(10):
        for j in range(10):
            k=i*10+j
            for other in ([k+1] if j<9 else []) + ([k+10] if i<9 else []):
                row=np.zeros(100); row[k]=-1; row[other]=1; rows.append(row)
    return np.asarray(rows)


class Inverse:
    def __init__(self,A,eta=None):
        A=np.asarray(A,dtype=float)
        validate(A,np.zeros((3,128)))
        self.A=A; self.L=gradient_matrix()
        one=np.ones((100,1))/np.sqrt(100)
        self.P=np.eye(100)-one@one.T
        self.eta0=1e-2*np.linalg.norm(A,2)**2/np.linalg.norm(self.L,2)**2
        self.eta=self.eta0 if eta is None else float(eta)
        if not np.isfinite(self.eta) or self.eta<=0:
            raise ValueError('Positive finite regularisation required')
        self.M=self.P@(A.T@A+self.eta*(self.L.T@self.L))@self.P+1e-9*np.eye(100)

    def solve(self,data):
        data=np.asarray(data,dtype=float)
        if data.ndim not in (1,2) or data.shape[-1]!=128 or not np.isfinite(data).all():
            raise ValueError('Expected finite (...,128) data with one optional batch dimension')
        # Multiple RHS use exactly the same least-squares system as one RHS.
        b=self.P@(self.A.T@data.T)
        m=np.linalg.lstsq(self.M,b,rcond=None)[0].T
        return m-m.mean(axis=-1,keepdims=True)


def equivalent_fwhm(image,position):
    image=np.asarray(image).reshape(10,10)
    xx,yy=np.meshgrid(COORD,COORD)
    row,col=position
    r2=(xx-COORD[col])**2+(yy-COORD[row])**2
    w=np.maximum(image,0)
    if not np.isfinite(w).all() or w.sum()<=0:
        raise ValueError('Point response has no finite positive weight')
    return float(2.355*np.sqrt(np.sum(w*r2)/(2*w.sum())))


def point_spread(inverse,position):
    q=np.zeros((10,10)); q[position]=1; q-=q.mean()
    psf=inverse.solve(inverse.A@q.ravel()).reshape(10,10)
    return q.ravel(),psf,equivalent_fwhm(psf,position)


def noise_limit(inverse,repeats,seed=SEED):
    validate(inverse.A,repeats)
    sigma=repeats.std(axis=0,ddof=1)
    noise=np.random.default_rng(seed).normal(0,sigma,(NOISE_DRAWS,128))
    maps=inverse.solve(noise)
    maxima=np.max(abs(maps),axis=1)
    return dict(sigma=sigma,noise=noise,maps=maps,maxima=maxima,
                delta95=float(np.percentile(maxima,95)))


def features(m):
    m=np.asarray(m).reshape(100)
    result=[]
    for sign,k in [('positive',int(m.argmax())),('negative',int(m.argmin()))]:
        if (sign=='positive' and m[k]<=0) or (sign=='negative' and m[k]>=0):
            continue
        row,col=divmod(k,10)
        result.append(dict(sign=sign,row=row,column=col,x_probe_pitch=float(COORD[col]),
                           y_probe_pitch=float(COORD[row]),amplitude_fraction=float(m[k])))
    return result


def decision(amplitude,delta95,threshold):
    if not np.isfinite([amplitude,delta95]).all() or min(amplitude,delta95)<0:
        raise ValueError('Amplitude and detection limit must be finite and non-negative')
    if threshold is None:
        return {'pass':None,'status':'pending_threshold',
                'confidence':'NOT FINAL: classroom threshold missing; pass/fail decision pending.'}
    if not np.isfinite(threshold) or threshold<=0:
        raise ValueError('L3 threshold must be finite and positive')
    if amplitude+delta95 < threshold:
        status,passed='clear_pass',True
    elif amplitude-delta95 > threshold:
        status,passed='clear_fail',False
    else:
        status,passed='borderline',None
    return {'pass':passed,'status':status,'confidence':
            f'{status}: a={amplitude:.12g}, delta95={delta95:.12g}, threshold={threshold:.12g}; '
            'guide noise-margin rule, not a posterior pass probability.'}


def analyse(A,repeats,threshold=None):
    validate(A,repeats)
    inv=Inverse(A); mean=repeats.mean(axis=0); m=inv.solve(mean)
    scan=[]
    for factor in MULTIPLIERS:
        eta=inv.eta0*factor
        candidate=Inverse(A,eta).solve(mean)
        scan.append(dict(multiplier=factor,eta=eta,map=candidate,
                         residual=float(np.linalg.norm(A@candidate-mean)),
                         roughness=float(np.linalg.norm(inv.L@candidate))))
    psfs=[dict(position=pos,response=point_spread(inv,pos)) for pos in [(5,5),(2,2)]]
    noise=noise_limit(inv,repeats)
    a=float(np.max(abs(m)))
    return dict(inverse=inv,mean=mean,map=m,scan=scan,psfs=psfs,noise=noise,
                features=features(m),amplitude=a,decision=decision(a,noise['delta95'],threshold),
                resolution=max(x['response'][2] for x in psfs),
                singular_values=np.linalg.svd(A,compute_uv=False))
