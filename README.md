# point-alpaca

<img src="https://point-alpaca.fra1.cdn.digitaloceanspaces.com/alpaca.png" height="200" width="200">

## What is this?

This is released weights recreated from [Stanford Alpaca](https://github.com/tatsu-lab/stanford_alpaca), an experiment in fine-tuning LLaMA on a synthetic instruction dataset.

## Can I try this somewhere?

Yes! Announcement thread to our frontend where you can try the 7B: https://twitter.com/PointNetwork/status/1637178814210908160

## How to distill the weights

1. Put LLaMA weights into `original/` folder, such that 7B version would be at `original/7B`

2. Download point-alpaca diffs into `encrypted/` folder:

```
wget -P encrypted/ -i filelist.txt
```

3. Run the following command to decrypt:

```
for f in "encrypted"/*; do if [ -f "$f" ]; then python3 decrypt.py "$f" "original/7B/consolidated.00.pth" "result/"; fi; done
```

Windows users can use the equivalent powershell command: 

```
Get-ChildItem "encrypted" | ForEach-Object {
    if($_.Attributes -eq 'Archive') {
        python3 decrypt.py $_.FullName "original/7B/consolidated.00.pth" "result/"
    }
}
```

You will have finetuned weights in the `result/` folder.

Now that you have them, you can delete the files in `encrypted/` folder.

## How to chat with the model

Other people will probably build better UIs, but for now, try running `python3 chat.py`

But before that, install requirements via `pip3 install -r requirements.txt` (We really recommend installing it in a separate environment, for example, via `conda`)

## Questions? Suggestions?

Find us in our Telegram chat: https://t.me/pointnetworkchat

## Why are weights "encrypted"?

We are not allowed to publish weights for LLaMA, of course, even finetuned, but there is no problem publishing *the difference*, a patch that we suggest to apply to the files. The encryption is a simple XOR between files (not very secure - not recommended for other applications!), ensuring that only the people that have access to the original weights (from completely legal sources, of course) can transform them into finetuned weights.

## What about larger models?

13B is coming for sure, larger versions - maybe. Consider supporting us if you want it done faster. :)
